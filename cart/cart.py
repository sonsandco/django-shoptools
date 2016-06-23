import uuid
from datetime import datetime
import decimal
import importlib

from django.apps import apps
from django.conf import settings
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
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
# the SessionCart and the Order object should share an interface
# so should SessionCartLine and OrderLine
# in a template we should be able to treat a db-saved or session "cart"
# exactly the same
# BUT are interfaces "pythonic"? Should these be ABCs?

# This file is getting unwieldy, need to split into cart.session and
# cart.cart or something like that

# Rather than raising NotImplementedError for things like total and
# shipping_cost, we should check using hasattr and ignore if they're not there


@property
def NotImplementedProperty(self):
    raise NotImplementedError


class ICartItem(object):
    """Define interface for objects which may be added to a cart. """

    def cart_errors(self, line):
        return []

    def cart_description(self):
        raise NotImplementedError()

    def cart_line_total(self, qty, order_obj):
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
           get_voucher_codes

       """

    def add(self, ctype, pk, qty=1):
        return self.update_quantity(ctype, pk, qty, add=True)

    def remove(self, ctype, pk):
        return self.update_quantity(ctype, pk, 0)

    def get_errors(self):
        """Validate each cart line item. Subclasses may override this method
           to perform whole-cart validation. Return a list of error strings
        """

        errors = []
        for line in self.get_lines():
            errors += line.get_errors()
        return errors

    def as_dict(self):
        data = {
            'count': self.count(),
            'lines': [line.as_dict() for line in self.get_lines()],
            # TODO add discounts?
        }
        for f in ('subtotal', 'shipping_cost', 'total'):
            if hasattr(self, f):
                data[f] = float(getattr(self, f) or 0)
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
    def calculate_discounts(self, invalid=False, include_shipping=True):
        voucher_module = get_voucher_module()
        if voucher_module:
            return voucher_module.calculate_discounts(
                self, self.get_voucher_codes(), invalid=invalid,
                include_shipping=include_shipping)
        return []

    @property
    def total_discount(self):
        return sum(d.amount for d in self.calculate_discounts())

    def save_to(self, obj):
        assert isinstance(obj, BaseOrder)

        [l.delete() for l in obj.get_lines()]
        for cart_line in self.get_lines():
            line = obj.get_line_cls()()
            line.parent_object = obj
            line.item = cart_line.item
            line.quantity = cart_line.quantity
            line.currency = self.currency
            line.save()

        # save valid discounts - TODO should this go here?
        # Do we need to subclass Cart as DiscountCart?
        from checkout.models import Order
        if isinstance(obj, Order):
            voucher_module = get_voucher_module()
            vouchers = self.get_voucher_codes() if voucher_module else None
            if vouchers:
                [d.delete() for d in obj.discount_set.all()]
                voucher_module.save_discounts(obj, vouchers)

        # save shipping info - cost calculated automatically
        if hasattr(obj, 'set_shipping'):
            obj.set_shipping(self.shipping_options)


class ICartLine(object):
    """Define interface for cart lines, which are attached to an ICart.
       Subclasses must implement the following properties

       item
       quantity
       total
       description
       parent_object

    """

    def get_errors(self):
        """Validate this line's item. Return a list of error strings"""
        return self.item.cart_errors(self)

    @property
    def ctype(self):
        # app.model, compatible with the ctype argument to Cart.update etc
        return '%s.%s' % (self.item._meta.app_label,
                          self.item._meta.model_name)

    def as_dict(self):
        return {
            'description': self.description,
            'quantity': self.quantity,
            'total': float(self.total),
        }


class BaseOrder(models.Model, ICart):
    """Base class for "Order" models, which are the db-saved version of a
       SessionCart. Theoretically, this model can be used interchangeably with
       the SessionCart, adding/removing items etc. """

    class Meta:
        abstract = True

    def update_quantity(self, ctype, pk, qty=1, add=False):
        if qty == 0 and add:
            return

        if not self.pk:
            # must be an unsaved instance; assume that it's ready to be saved
            self.save()

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
        if add:
            update_qty = models.F('quantity') + qty
        else:
            update_qty = qty
        updated = lines.update(quantity=update_qty)

        if not updated and qty:
            line_cls.objects.create(quantity=qty, **values)

        # purge any with a zero quantity after the update
        lines.filter(quantity__lte=0).delete()

        return True

    def get_line(self, ctype, pk):
        app_label, model = ctype.split('.')
        try:
            return self.get_lines().get(
                item_content_type__app_label=app_label,
                item_content_type__model=model,
                item_object_id=pk)
        except self.get_line_cls().DoesNotExist:
            return None

    def get_lines(self):
        return self.get_line_cls().objects.filter(parent_object=self)

    def empty(self):
        return not self.get_lines().count()

    def count(self):
        return self.get_lines().aggregate(c=models.Sum('quantity'))['c'] or 0

    def clear(self):
        # this doesn't have to delete the Order, it could hang around and
        # the lines could just be deleted
        # if we ever want to save details from one order to the next (shipping
        # options for example) do it here

        # return self.get_lines().delete()
        self.delete()

    @property
    def subtotal(self):
        return sum(line.total for line in self.get_lines())


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
    item_content_type = models.ForeignKey(ContentType,
                                          on_delete=models.PROTECT)
    item_object_id = models.PositiveIntegerField()
    item = GenericForeignKey('item_content_type', 'item_object_id')

    created = models.DateTimeField(default=datetime.now)
    quantity = models.IntegerField()
    # currency = models.CharField(max_length=3, editable=False,
    #    default=DEFAULT_CURRENCY)
    # total = models.DecimalField(max_digits=8, decimal_places=2)
    # description = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True
        unique_together = ('item_content_type', 'item_object_id',
                           'parent_object')

    @property
    def total(self):
        return decimal.Decimal(
            self.item.cart_line_total(self.quantity, self.parent_object))

    @property
    def description(self):
        return self.item.cart_description()

    def _str__(self):
        return "%s x %s: $%.2f" % (self.description, self.quantity,
                                   self.total)


def create_key(ctype, pk):
    return '|'.join((ctype, str(pk)))


def unpack_key(key):
    (ctype, pk) = key.split('|')
    return (ctype, pk)


def get_item_from_key(key):
    ctype, pk = unpack_key(key)
    content_type = ContentType.objects \
        .get_by_natural_key(*ctype.split("."))
    try:
        return content_type.get_object_for_this_type(pk=pk)
    except ObjectDoesNotExist:
        return None


class SessionCartLine(dict, ICartLine):
    '''Thin wrapper around dict providing some convenience methods for
       accessing computed information about the line, according to ICartLine.
    '''

    def __init__(self, **kwargs):
        assert sorted(kwargs.keys()) == ['key', 'parent_object', 'qty']
        return super(SessionCartLine, self).__init__(**kwargs)

    def __setitem__(self, *args):
        raise Exception("Sorry, SessionCartLine instances are immutable.")

    item = property(lambda s: get_item_from_key(s['key']))
    quantity = property(lambda s: s['qty'])
    total = property(lambda s: s.item.cart_line_total(s['qty'], s))
    description = property(lambda s: s.item.cart_description())
    parent_object = property(lambda s: s['parent_object'])


class SessionCart(ICart):
    """Default session-saved cart class. To implement multiple "carts" in one
       site using this class, pass a distinct session_key to the constructor
       for each. """

    def __init__(self, request, session_key=None):
        self.request = request
        self.session_key = session_key or DEFAULT_SESSION_KEY
        self.currency = request.COOKIES.get(CURRENCY_COOKIE_NAME,
                                            DEFAULT_CURRENCY)
        self._data = self.request.session.get(self.session_key, None)

    def get_voucher_codes(self):
        if self._data is None:
            return []
        return self._data.get('vouchers', [])

    def update_vouchers(self, codes):
        self._init_session_cart()
        self._data["vouchers"] = list(codes)
        self.request.session.modified = True
        return True

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

    def update_quantity(self, ctype, pk, qty=1, add=False):
        assert isinstance(qty, int)
        idx = self._line_index(ctype, pk)

        if add and idx is not None:
            qty += self._data["lines"][idx]['qty']

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

    def get_line(self, ctype, pk):
        idx = self._line_index(ctype, pk)
        if idx is None:
            return None
        return SessionCartLine(parent_object=self, **self._data["lines"][idx])

    def get_lines(self):
        if self._data is None:
            return
        for line in self._data["lines"]:
            line = SessionCartLine(parent_object=self, **line)
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

    def set_order_obj(self, obj):
        self._data['order_obj'] = '%s.%s|%s' % (
            obj._meta.app_label, obj._meta.model_name, obj.pk)
        self.request.session.modified = True

    def get_order_obj(self):
        if self._data is None:
            return None

        key = self._data.get('order_obj')
        return get_item_from_key(key) if key else None

    order_obj = property(get_order_obj, set_order_obj)

    def empty(self):
        return not bool(len(list(self.get_lines())))

    def clear(self):
        if self._data is not None:
            del self.request.session[self.session_key]
            self._data = None

    def save_to(self, obj):
        super(SessionCart, self).save_to(obj)

        # link the order to the cart
        self.order_obj = obj

    # Private methods
    def _init_session_cart(self):
        if self._data is None:
            data = {'lines': []}
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


def make_uuid():
    u = uuid.uuid4()
    return str(u).replace('-', '')


def get_cart(request):
    """Get the current cart - if the cart app is installed, and user is logged
       in, return a db cart (which may be an unsaved instance). Otherwise,
       return a session cart.

       If there's items in the session_cart, merge them into the db cart.
    """

    session_cart = SessionCart(request)

    if apps.is_installed('cart') and request.user.is_authenticated():

        # django doesn't like this to be imported at compile-time if the app is
        # not installed
        from .models import SavedCart

        try:
            cart = SavedCart.objects.get(user=request.user)
        except SavedCart.DoesNotExist:
            cart = SavedCart(user=request.user)

        cart.set_request(request)

        # merge session cart, if it exists
        if session_cart.count():
            if not cart.pk:
                cart.save()
            session_cart.save_to(cart)
            session_cart.clear()
        return cart

    return session_cart
