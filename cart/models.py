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
SHIPPING_MODULE = getattr(settings, 'CART_SHIPPING_MODULE', None)
VOUCHER_MODULE = getattr(settings, 'CART_VOUCHER_MODULE', None)


def get_voucher_module():
    return importlib.import_module(VOUCHER_MODULE) if VOUCHER_MODULE else None


def get_shipping_module():
    return importlib.import_module(SHIPPING_MODULE) \
        if SHIPPING_MODULE else None


# TODO
# the Cart and the Order object should share an interface
# so should CartLine and OrderLine
# in a template we should be able to treat a db-saved or session "cart"
# exactly the same
# BUT are interfaces "pythonic"? Should these be ABCs?

# This file is getting unwieldy, need to split into cart.session and
# cart.models or something like that

# Rather than raising NotImplementedError for things like total and
# shipping_cost, we should check using hasattr and ignore if they're not there


@property
def NotImplementedProperty(self):
    raise NotImplementedError


class ICartItem(object):
    """Define interface for objects which may be added to a cart. """

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
    """Define interface for "cart" objects, which may be a session-based
       "cart" or a db-saved "order".

       Subclasses should implement the following:

           update_quantity(self, ctype, pk, qty)
           clear(self)
           count(self)
           get_lines(self)

       and may implement the following (optional):

           subtotal
           total
           shipping_cost

       """

    def add(self, ctype, pk, qty=1):
        return self.update_quantity(ctype, pk, qty)

    def remove(self, ctype, pk):
        return self.update_quantity(ctype, pk, 0)

    def as_dict(self):
        data = {
            'count': self.count(),
            'lines': [line.as_dict() for line in self.get_lines()],
            # TODO add discounts?
        }
        for f in ('shipping_cost', 'total'):
            if hasattr(self, f):
                data[f] = float(getattr(self, f))
        return data

    def update_quantity(self, ctype, pk, qty):
        raise NotImplementedError()

    def get_lines(self):
        raise NotImplementedError()

    def count(self):
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()

    # TODO tidy up discount stuff - does it belong here?
    def calculate_discounts(self):
        raise NotImplementedError()

    @property
    def total_discount(self):
        return sum(d.amount for d in self.calculate_discounts())


class ICartLine(object):
    """Define interface for cart lines, which are attached to an ICart.
       Subclasses must implement the following properties

       item
       quantity
       total
       description
    """

    def as_dict(self):
        return {
            'description': self.description,
            'quantity': self.quantity,
            'total': float(self.total),
        }


class BaseOrder(models.Model, ICart):
    """Base class for "Order" models, which are the db-saved version of a
       session Cart. Theoretically, this model can be used interchangeably with
       the Cart, adding/removing items etc. """

    class Meta:
        abstract = True

    def update_quantity(self, ctype, pk, qty=1):
        app_label, model = ctype.split('.')
        try:
            ctype_obj = ContentType.objects.get(app_label=app_label,
                                                model=model)
        except ContentType.DoesNotExist:
            return False

        values = {
            'parent_object': self,
            'item_content_type': ctype_obj,
            'item_object_id': pk,
        }
        line_cls = self.get_line_cls()
        lines = line_cls.objects.filter(**values)
        if qty < 1:
            lines.delete()
        else:
            updated = lines.update(quantity=qty)
            if not updated:
                line_cls.objects.create(quantity=qty, **values)

        return True

    def get_lines(self):
        return self.get_line_cls().objects.filter(parent_object=self)

    def count(self):
        return self.get_lines().count()

    def clear(self):
        return self.get_lines().delete()


class BaseOrderLine(models.Model, ICartLine):
    """An OrderLine is the db-persisted version of a Cart line, created by
    subclassing this model. It implements the same ICartLine interface as the
    cart lines, and is intended to be attached to an object you provide via
    a parent_object ForeignKey. Your object can be thought of as an Order,
    although it doesn't have to be; it could equally support a "save this cart
    for later" feature.

    Subclasses must implement a parent_object ForeignKey
    """

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

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        assert isinstance(self.item, ICartItem)

        if self.total is None:
            # if the parent has a currency field, use it
            currency = getattr(self.parent_object, 'currency',
                               DEFAULT_CURRENCY)
            self.total = self.item.cart_line_total(self.quantity, currency)

        if self.description is None:
            self.description = self.item.cart_description()

        return super(BaseOrderLine, self).save(*args, **kwargs)

    def __unicode__(self):
        return u"%s x %s: $%.2f" % (self.description, self.quantity,
                                    self.total)


def create_key(ctype, pk):
    return u'|'.join((ctype, unicode(pk)))


def unpack_key(key):
    (ctype, pk) = key.split('|')
    return (ctype, pk)


def get_item_from_key(key):
    ctype, pk = unpack_key(key)
    content_type = ContentType.objects \
        .get_by_natural_key(*ctype.split("."))
    return content_type.get_object_for_this_type(pk=pk)


class CartLine(dict, ICartLine):
    '''Thin wrapper around dict providing some convenience methods for
       accessing computed information about the line, according to ICartLine.
    '''

    def __init__(self, **kwargs):
        assert sorted(kwargs.keys()) == ['currency', 'key', 'qty']
        return super(CartLine, self).__init__(**kwargs)

    def __setitem__(self, *args):
        raise Exception(u"Sorry, CartLine instances are immutable.")

    item = property(lambda s: get_item_from_key(s['key']))
    quantity = property(lambda s: s['qty'])
    total = property(lambda s: s.item.cart_line_total(s['qty'], s['currency']))
    description = property(lambda s: s.item.cart_description())


class Cart(ICart):
    def __init__(self, request, session_key=None):
        self.request = request
        self.session_key = session_key or DEFAULT_SESSION_KEY
        self.currency = request.COOKIES.get(CURRENCY_COOKIE_NAME,
                                            DEFAULT_CURRENCY)
        self._data = self.request.session.get(self.session_key, None)

    def get_voucher_codes(self):
        if self._data is None:
            return []
        return self._data["vouchers"]

    def update_vouchers(self, codes):
        self._init_session_cart()
        self._data["vouchers"] = list(codes)
        self.request.session.modified = True
        return True

    def calculate_discounts(self, invalid=False):
        voucher_module = get_voucher_module()
        if voucher_module:
            return voucher_module.calculate_discounts(
                self, self.get_voucher_codes(), invalid=invalid)
        return []

    @property
    def shipping_options(self):
        shipping_module = get_shipping_module()
        if shipping_module:
            return shipping_module.get_session(self.request)
        return {}

    @property
    def shipping_cost(self):
        shipping_module = get_shipping_module()
        if shipping_module:
            return shipping_module.calculate_shipping(self)
        return 0

    def update_quantity(self, ctype, pk, qty=1):
        assert isinstance(qty, int)
        idx = self._line_index(ctype, pk)

        if qty < 1:
            if idx is None:
                return False
            del self._data["lines"][idx]
            self.request.session.modified = True
            return True

        if idx is None:
            self._init_session_cart()
            line = {'key': create_key(ctype, pk), 'qty': qty}
            self._data["lines"].append(line)
        else:
            # Already in the cart, so update the existing line
            line = self._data["lines"][idx]['qty'] = qty

        self.request.session.modified = True
        return True

    def get_lines(self):
        if self._data is None:
            return
        for line in self._data["lines"]:
            line = CartLine(currency=self.currency, **line)
            if line.item:
                yield line

    def count(self):
        if self._data is None:
            return 0
        return sum(r['qty'] for r in self._data["lines"])

    @property
    def subtotal(self):
        if self._data is None:
            return 0
        return decimal.Decimal(
            sum(line.total for line in self.get_lines()))

    @property
    def total(self):
        return self.subtotal + self.shipping_cost - self.total_discount

    def save_to(self, obj):
        assert isinstance(obj, ICart)
        assert self._data and (self._data.get("lines", None) is not None)

        for cart_line in self.get_lines():
            line = obj.get_line_cls()()
            line.parent_object = obj
            line.item = cart_line.item
            line.description = cart_line.description
            line.quantity = cart_line["qty"]
            line.currency = self.currency
            line.save()

        # save valid discounts - TODO should this go here?
        # Do we need to subclass Cart as DiscountCart?
        voucher_module = get_voucher_module()
        vouchers = self.get_voucher_codes() if voucher_module else None
        if vouchers:
            voucher_module.save_discounts(obj, vouchers)

    def empty(self):
        return not bool(len(self.get_lines()))

    def clear(self):
        if self._data is not None:
            del self.request.session[self.session_key]
            self._data = None

    # Private methods
    def _init_session_cart(self):
        if self._data is None:
            data = {"lines": [], "vouchers": []}
            self._data = self.request.session[self.session_key] = data

    def _line_index(self, ctype, pk):
        """Returns the line index for a given ctype/pk, if it's already in the
           cart, or None otherwise."""

        app_label, model = ctype.split('.')
        assert issubclass(
            ContentType.objects.get(
                app_label=app_label, model=model).model_class(),
            ICartItem)

        if self._data is not None:
            for i in range(len(self._data["lines"])):
                if self._data["lines"][i]["key"] == create_key(ctype, pk):
                    return i
        return None
