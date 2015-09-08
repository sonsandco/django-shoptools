from datetime import datetime
import decimal
import importlib

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


DEFAULT_SESSION_KEY = getattr(settings, 'CART_DEFAULT_SESSION_KEY', 'cart')
DEFAULT_CURRENCY = getattr(settings, 'DEFAULT_CURRENCY', 'NZD')
CURRENCY_COOKIE_NAME = getattr(settings, 'CURRENCY_COOKIE_NAME', None)
SHIPPING_CALCULATOR = getattr(settings, 'CART_SHIPPING_CALCULATOR', None)


# TODO
# the Cart and the Order object should share an interface
# so should CartRow and OrderLine
# in a template we should be able to treat a db-saved or session "cart"
# exactly the same


@property
def NotImplementedProperty(self):
    raise NotImplementedError


class ICartItem(object):
    """Defines interface for objects which may be added to a cart. """

    def cart_description(self):
        raise NotImplementedError()

    def cart_reference(self):
        raise NotImplementedError()

    def cart_line_total(self, qty, currency):
        # currently must return a float/int, not decimal, due to django's
        # serialization limitations - see
        # https://docs.djangoproject.com/en/1.8/topics/http/sessions/#session-serialization
        raise NotImplementedError()


class ICart(object):
    """Define interface for "cart" objects, which may be db or session. """

    # TODO - fill out


class ICartLine(object):
    """Define interface for cart lines, which are attacehd to an ICart. """

    # TODO - fill out

    item = NotImplementedProperty


class BaseOrderLine(models.Model, ICartLine):
    """An OrderLine is the db-persisted version of a Cart item, created by
    subclassing this model. It uses the same ICartItem interface (see below)
    to get details, and is intended to be attached to an object you provide via
    a parent_object ForeignKey. Your object can be thought of as an Order,
    although it doesn't have to be; it could equally support a "save this cart
    for later" feature.

    The advantage of this is that is lets your shop app support
    whatever payment/total cost logic it wants -- it might be a
    straight summing of order lines, it might add shipping, it might
    not involve payment at all.

    This only handles recording items + quantities + calculated prices
    against some object.
    """

    parent_object = NotImplementedProperty

    # item object *must* support ICartItem
    item_content_type = models.ForeignKey(ContentType)
    item_object_id = models.PositiveIntegerField()
    item = GenericForeignKey('item_content_type', 'item_object_id')

    created = models.DateTimeField(default=datetime.now)
    quantity = models.IntegerField()
    # currency = models.CharField(max_length=3, editable=False,
    #    default=DEFAULT_CURRENCY)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    options = models.TextField(blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        assert isinstance(self.item, ICartItem)

        if not self.total:
            # if the parent has a currency field, use it
            currency = getattr(self.parent_object, 'currency',
                               DEFAULT_CURRENCY)
            self.total = self.item.cart_line_total(self.quantity, currency)

        if not self.description:
            self.description = self.item.cart_description()

        return super(BaseOrderLine, self).save(*args, **kwargs)

    def __unicode__(self):
        return u"%s x %s: $%.2f" % (self.description, self.quantity,
                                    self.total)


class CartRow(dict, ICartLine):
    '''Thin wrapper around dict providing some convenience methods for
       accessing computed information about the row.'''

    def __init__(self, **kwargs):
        assert sorted(kwargs.keys()) == ['key', 'line_total', 'options', 'qty']
        return super(CartRow, self).__init__(**kwargs)

    def __setitem__(self, *args):
        raise Exception(u"Sorry, CartRow instances are immutable.")

    @property
    def item(self):
        return Cart.get_item(self['key'])

    def line_total(self):
        return self['line_total']
        # return self.item.cart_line_total(self['qty'], currency)

    def description(self):
        return self.item.cart_description()


class Cart(ICart):
    def __init__(self, request, session_key=None):
        self.request = request
        self.session_key = session_key or DEFAULT_SESSION_KEY
        self.currency = request.COOKIES.get(CURRENCY_COOKIE_NAME,
                                            DEFAULT_CURRENCY)
        self._data = self.request.session.get(self.session_key, None)

    def _init_session_cart(self):
        if self._data is None:
            data = {"rows": []}
            self._data = self.request.session[self.session_key] = data

    def as_dict(self):
        data = {
            'count': self.count(),
            'shipping_cost': self.shipping_cost(),
            'total': str(self.total()),
            'lines': [],
        }
        for row in self.rows():
            line = dict(row)
            line.update({
                'item': unicode(row.item),
                'line_total': row.line_total(),
            })
            data['lines'].append(line)
        return data

    def empty(self):
        return self._data is None or len(self._data["rows"]) is 0

    def update_shipping(self, options):
        self._init_session_cart()
        self._data["shipping"] = options
        self.request.session.modified = True
        return True

    def get_shipping_options(self):
        return (self._data or {}).get("shipping", {})

    def add(self, ctype, pk, qty=1, opts={}):
        app_label, model = ctype.split('.')
        ctype_obj = ContentType.objects.get(app_label=app_label, model=model)
        assert issubclass(ctype_obj.model_class(), ICartItem)

        try:
            qty = int(qty)
        except TypeError:
            qty = 1

        idx = self.row_index(ctype, pk)
        if idx is not None:
            # Already in the cart, so update the existing row
            row = self._data["rows"][idx]
            return self.update_quantity(ctype, pk, qty + row["qty"])

        self._init_session_cart()
        row = {'key': Cart.create_key(ctype, pk), 'qty': qty, 'options': opts}
        self._data["rows"].append(row)
        # self.update_total()
        self.request.session.modified = True
        return True

    def row_index(self, ctype, pk):
        """Returns the row index for a given ctype/pk, if it's already in the
           cart, or None otherwise."""

        if self._data is not None:
            for i in range(len(self._data["rows"])):
                if self._data["rows"][i]["key"] == self.create_key(ctype, pk):
                    return i
        return None

    def remove(self, ctype, pk):
        idx = self.row_index(ctype, pk)
        if idx is not None:  # might be 0
            del self._data["rows"][idx]
            # self.update_total()
            self.request.session.modified = True
            return True

        return False

    def update_options(self, ctype, pk, **options):
        idx = self.row_index(ctype, pk)
        if idx is not None:  # might be 0
            self._data["rows"][idx]['options'].update(options)
            self.request.session.modified = True
            return True

        return False

    def update_quantity(self, ctype, pk, qty):
        idx = self.row_index(ctype, pk)
        if idx is not None:  # might be 0
            self._data["rows"][idx]['qty'] = qty
            # self.update_total()
            self.request.session.modified = True
            return True

        return False

    @staticmethod
    def get_item(key):
        ctype, pk = Cart.unpack_key(key)
        content_type = ContentType.objects \
            .get_by_natural_key(*ctype.split("."))
        return content_type.get_object_for_this_type(pk=pk)

    @staticmethod
    def create_key(ctype, pk):
        return u'|'.join((ctype, unicode(pk)))

    @staticmethod
    def unpack_key(key):
        (ctype, pk) = key.split('|')
        return (ctype, pk)

    def row(self, **data):
        assert sorted(data.keys()) == ['key', 'options', 'qty']
        item = self.get_item(data['key'])
        data['line_total'] = item.cart_line_total(data['qty'], self.currency)
        return CartRow(**data)

    def rows(self):
        if self._data is None:
            return []
        return [self.row(**row) for row in self._data["rows"]]

    def count(self):
        if self._data is None:
            return 0
        return sum(r['qty'] for r in self._data["rows"])

    def shipping_cost(self):
        if SHIPPING_CALCULATOR:
            bits = SHIPPING_CALCULATOR.split('.')
            calc_module = importlib.import_module('.'.join(bits[:-1]))
            calc_func = getattr(calc_module, bits[-1])
            shipping_options = self.get_shipping_options()
            return calc_func(self.rows(), options=shipping_options)
        return 0

    def subtotal(self):
        if self._data is None:
            return 0
        return decimal.Decimal(sum(row.line_total() for row in self.rows()))

    def total(self):
        return self.subtotal() + self.shipping_cost()

    def save_to(self, obj, orderline_model_cls):
        assert isinstance(obj, ICart)
        assert issubclass(orderline_model_cls, ICartItem)
        assert self._data and (self._data.get("rows", None) is not None)
        for row in self.rows():
            line = orderline_model_cls()
            line.parent_object = obj
            line.item = row.item
            line.quantity = row["qty"]
            line.currency = self.currency
            line.options = unicode(row["options"])
            line.save()

    def clear(self):
        if self._data is not None:
            del self.request.session[self.session_key]
            self._data = None
