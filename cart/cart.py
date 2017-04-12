import uuid
from datetime import datetime
import decimal
import importlib
import json

from django.apps import apps
from django.conf import settings
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.postgres.fields import JSONField

from .util import get_cart_html


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

    def purchase(self, line):
        """Called on successful purchase. """
        pass

    def cart_errors(self, line):
        """Used by the cart and checkout to check for errors, i.e. out of
           stock. """
        return []

    def cart_description(self):
        """Describes the item in the checkout admin. Needed because the needs
           to store a description of the item as purchased, even if it is
           deleted or changed down the track. """
        raise NotImplementedError()

    def cart_line_total(self, line):
        """Returns the total price for qty of this item. """

        # currently must return a float/int, not decimal, due to django's
        # serialization limitations - see
        # https://docs.djangoproject.com/en/1.8/topics/http/sessions/#session-serialization
        raise NotImplementedError()

    def available_options(self):
        """Available purchase options for the product - product variants
           should generally be preferred over this system. Use options where
           it doesn't make sense for the different option to be represented
           by a different instance, i.e. "Add monogramming", or need to be
           ad-hoc, i.e. specific to the product instance rather than
           the model.

           NOTE values must be strings because that's what gets posted through
           from forms. TODO fix this. Do we enforce json payloads from the
           frontend?

           Example:

           {
               'color': ['red', 'black'],
               'size': ['S', 'M', 'L'],
           }
        """

        return {}

    def default_options(self):
        """Return a dict of defaults, by default this just takes the first
           option from each. """

        return dict((key, opts[0]) for key, opts in self.available_options())

    @property
    def ctype(self):
        # app.model, compatible with the ctype argument to Cart.add etc
        return '%s.%s' % (self._meta.app_label,
                          self._meta.model_name)

    # @property
    # def unique_identifier(self):
    #     # unique across all models, intended for use as an id or class
    #     # attribute where the ability to get a specific item is required
    #     return self.ctype.replace('.', '-') + '-%d' % self.id


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
           get_shipping_options
           set_shipping_options
           get_voucher_codes

       """

    def add(self, ctype, pk, qty=1, options={}):
        return self.update_quantity(ctype, pk, qty, add=True, options=options)

    def remove(self, ctype, pk, options={}):
        return self.update_quantity(ctype, pk, 0, options=options)

    def get_errors(self):
        """Validate each cart line item. Subclasses may override this method
           to perform whole-cart validation. Return a list of error strings
        """

        errors = []
        for line in self.get_lines():
            errors += line.get_errors()

        errors += self.shipping_errors()

        return errors

    @property
    def is_valid(self):
        return self.count() and not self.get_errors()

    def as_dict(self):
        """Return dict of data for this cart instance, for json serialization.
           subclasses should override this method. """

        data = {
            'count': self.count(),
            'lines': [line.as_dict() for line in self.get_lines()],
        }

        if hasattr(self, 'get_shipping_options'):
            data['shipping_options'] = self.get_shipping_options()

        for f in ('subtotal', 'total'):
            if hasattr(self, f):
                attr = getattr(self, f)
                data[f] = float(attr) if attr is not None else None

        # TODO add discounts?

        data['html_snippet'] = get_cart_html(self)

        return data

    def update_quantity(self, ctype, pk, qty, options={}):
        raise NotImplementedError()

    def get_lines(self):
        """Return all valid lines (i.e. exclude those where the item is
           not valid or deleted) """
        raise NotImplementedError()

    def count(self):
        """Sum the quantities of all valid lines. """
        raise NotImplementedError()

    def clear(self):
        """Delete all cart lines. """
        raise NotImplementedError()

    # def set_shipping_options(self, options):
    #     """Save the provided options
    #
    #     Assume the options have already been validated, if necessary.
    #     """
    #
    #     raise NotImplementedError()
    #
    # def get_shipping_options(self):
    #     """Get shipping options, if any. """
    #
    #     raise NotImplementedError()

    @property
    def shipping_cost(self):
        shipping_module = get_shipping_module()
        if shipping_module:
            return shipping_module.calculate(self)
        return 0

    def shipping_errors(self):
        shipping_module = get_shipping_module()
        if shipping_module:
            return shipping_module.get_errors(self)
        return []

    # TODO tidy up discount stuff - does it belong here?
    def calculate_discounts(self, include_shipping=True):
        voucher_module = get_voucher_module()
        if voucher_module:
            return voucher_module.calculate_discounts(
                self, self.get_voucher_codes(),
                include_shipping=include_shipping)

    @property
    def total_discount(self):
        discounts, invalid = self.calculate_discounts()
        return sum(d.amount for d in discounts)

    def save_to(self, obj):
        assert isinstance(obj, BaseOrder)

        [l.delete() for l in obj.get_lines()]
        for cart_line in self.get_lines():
            line = obj.get_line_cls()()
            line.parent_object = obj
            line.item = cart_line.item
            line.options = cart_line.options
            line.quantity = cart_line.quantity
            line.currency = self.currency
            line.save()

        # save shipping info - cost calculated automatically
        if hasattr(obj, 'set_shipping_options'):
            # No need to validate options here, as was done when they were
            # saved to self.
            obj.set_shipping_options(self.get_shipping_options())

        # save valid discounts - TODO should this go here?
        # Do we need to subclass Cart as DiscountCart?
        from checkout.models import Order
        if isinstance(obj, Order):
            voucher_module = get_voucher_module()
            vouchers = self.get_voucher_codes() if voucher_module else None
            if vouchers:
                [d.delete() for d in obj.discount_set.all()]
                voucher_module.save_discounts(obj, vouchers)


class IShippable(object):
    # TODO - maybe move shipping stuff in here?
    pass


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
        return self.item.cart_errors(self) if self.item else []

    @property
    def ctype(self):
        # app.model, compatible with the ctype argument to Cart.update etc
        return '%s.%s' % (self.item._meta.app_label,
                          self.item._meta.model_name)

    # @property
    # def item_id(self):
    #     return self.item.pk

    # @property
    # def unique_identifier(self):
    #     # unique across all models, intended for use as an id or class
    #     # attribute where the ability to get a specific item is required
    #     return self.ctype.replace('.', '-') + '-%d' % self.item.id

    def options_text(self):
        # TODO handle the case where options is blank i.e. ''
        return ', '.join('%s: %s' % opt for opt in self.options.items())

    def as_dict(self):
        return {
            'description': self.description,
            'options': self.options,
            'quantity': self.quantity,
            'total': float(self.total),
            # 'unique_identifier': self.unique_identifier if self.item else None,
        }


class BaseOrder(models.Model, ICart):
    """Base class for "Order" models, which are the db-saved version of a
       SessionCart. Theoretically, this model can be used interchangeably with
       the SessionCart, adding/removing items etc. """

    class Meta:
        abstract = True

    def update_quantity(self, ctype, pk, qty=1, add=False, options={}):
        # TODO should validation happen here? Should probably be a separate
        # layer, and this function should assume valid input (ref django's
        # Model.save and Model.clean)

        # TODO purge 'add' argument
        if qty == 0 and add:
            return (False, 'No quantity specified')

        if not self.pk:
            # must be an unsaved instance; assume that it's ready to be saved
            self.save()

        line = self.get_line(ctype, pk, options, create=True)

        # qty may be an addition or a straight update
        if add:
            line.quantity = (line.quantity or 0) + qty
        else:
            line.quantity = qty

        # purge if quantity is zero after the update
        if not line.quantity:
            # may have been created on the fly if it didn't exist
            if line.pk:
                line.delete()
            return (True, None)

        # verify the order line object before saving
        errors = line.get_errors()
        if errors:
            return (False, errors)

        line.save()
        return (True, None)

    def get_line(self, ctype, pk, options, create=False):
        """This method should always be used to get a line, rather than
           directly via orm. """

        app_label, model = ctype.split('.')
        ctype_obj = ContentType.objects.get(app_label=app_label, model=model)
        lines = self.get_line_cls().objects.filter(parent_object=self)
        options = validate_options(ctype, pk, options)
        lookup = {
            'parent_object': self,
            # 'item_content_type__app_label': app_label,
            # 'item_content_type__model': model,
            'item_content_type': ctype_obj,
            'item_object_id': pk,
            'options': options,
        }
        try:
            line = lines.get(**lookup)
            # TODO think of a better way to solve this problem - saved orders
            # need to be decoupled from the request somehow. Save region etc
            # to the db in a json field?
            line.parent_object = self
            return line
        except self.get_line_cls().DoesNotExist:
            if create:
                return self.get_line_cls()(**lookup)
            return None

    def get_lines(self):
        """This method should always be used to get lines, rather than
           directly via orm. """

        lines = self.get_line_cls().objects.filter(parent_object=self) \
            .order_by('pk')
        for line in lines:
            if line.item:
                # parent_object may have been instantiated with a request,
                # so attach it to the line
                line.parent_object = self
                yield line

    def empty(self):
        return not self.count()

    def count(self):
        return sum(line.quantity for line in self.get_lines())

    def clear(self):
        # this doesn't have to delete the Order, it could hang around and
        # the lines could just be deleted
        # if we ever want to save details from one order to the next (shipping
        # options for example) do it here

        # return self.get_lines().delete()
        self.delete()

    @property
    def subtotal(self):
        return decimal.Decimal(sum(line.total for line in self.get_lines()))


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
    options = JSONField(default=dict, blank=True)

    # currency = models.CharField(max_length=3, editable=False,
    #    default=DEFAULT_CURRENCY)
    # total = models.DecimalField(max_digits=8, decimal_places=2)
    # description = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True
        # NOTE I'm relying on the jsonfield ordering its keys consistently
        unique_together = ('item_content_type', 'item_object_id',
                           'parent_object', 'options')

    @property
    def total(self):
        if not self.item:
            return decimal.Decimal(0)
        return decimal.Decimal(
            self.item.cart_line_total(self))

    @property
    def description(self):
        if not self.item:
            return ''
        return self.item.cart_description()

    def __str__(self):
        return "%s x %s: $%.2f" % (self.description, self.quantity,
                                   self.total)


def create_key(ctype, pk, options):
    options = validate_options(ctype, pk, options)
    return '|'.join((ctype, str(pk), json.dumps(options)))


def unpack_key(key):
    (ctype, pk, options) = key.split('|')
    return (ctype, pk, json.loads(options))


def get_instance(ctype, pk):
    content_type = ContentType.objects \
        .get_by_natural_key(*ctype.split("."))
    try:
        return content_type.get_object_for_this_type(pk=pk)
    except ObjectDoesNotExist:
        return None


def validate_options(ctype, pk, options):
    """Strip invalid options from an options dict. """

    # TODO this will eventually take an instance, not a ctype/pk

    content_type = ContentType.objects \
        .get_by_natural_key(*ctype.split("."))
    obj = content_type.get_object_for_this_type(pk=pk)
    available = obj.available_options()
    filtered = {k: v for k, v in options.items()
                if k in available and v in available[k]}

    # print (options, available, filtered)

    return filtered


class SessionCartLine(dict, ICartLine):
    '''Thin wrapper around dict providing some convenience methods for
       accessing computed information about the line, according to ICartLine.
    '''

    def __init__(self, **kwargs):
        assert sorted(kwargs.keys()) == ['key', 'options', 'parent_object',
                                         'qty']
        return super(SessionCartLine, self).__init__(**kwargs)

    def __setitem__(self, *args):
        raise Exception("Sorry, SessionCartLine instances are immutable.")

    @property
    def item(self):
        ctype, pk, options = unpack_key(self['key'])
        return get_instance(ctype, pk)

    options = property(lambda s: s['options'])
    quantity = property(lambda s: s['qty'])
    total = property(lambda s: s.item.cart_line_total(s))
    description = property(lambda s: s.item.cart_description())
    parent_object = property(lambda s: s['parent_object'])


class SessionCart(ICart, IShippable):
    """Default session-saved cart class. To implement multiple "carts" in one
       site using this class, pass a distinct session_key to the constructor
       for each. """

    def __init__(self, request, session_key=None):
        self.request = request
        self.session_key = session_key or DEFAULT_SESSION_KEY
        self._shipping_options = {}
        self.currency = request.COOKIES.get(CURRENCY_COOKIE_NAME,
                                            DEFAULT_CURRENCY)
        self._data = self.request.session.get(self.session_key, None)

    def get_voucher_codes(self):
        if self._data is None:
            return []
        return self._data.get('vouchers', [])

    def set_voucher_codes(self, codes):
        """Saves the provided voucher codes to this SessionCart. Assumes the
           codes have already been validated, if necessary.
        """

        self._init_session_cart()
        self._data["vouchers"] = list(codes)
        self.request.session.modified = True

    def set_shipping_options(self, options):
        """Saves the provided options to this SessionCart. Assumes the
           options have already been validated, if necessary.
        """

        self._init_session_cart()
        self._data['shipping'] = json.dumps(options)
        self.request.session.modified = True

    def get_shipping_options(self):
        """Get shipping options for this cart, if any, falling back to the
           shipping options saved against the session.
        """

        if self._data is None:
            return {}
        return json.loads(self._data.get('shipping', '{}'))

    # @property
    # def shipping_cost(self):
    #     return self.get_shipping_options().get('cost', None)

    # def validate_shipping(self):
    #     # TODO
    #     # return self.shipping_cost is not None

    def update_quantity(self, ctype, pk, qty=1, add=False, options={}):
        assert isinstance(qty, int)
        options = validate_options(ctype, pk, options)
        index = self._line_index(ctype, pk, options)

        # quantity may be additive or a straight update
        # TODO kill the add argument. cart.add should do this extra calculation
        if add and index is not None:
            qty += self._data["lines"][index]['qty']

        # purge if quantity is zero
        if qty < 1:
            if index is None:
                # fail silently
                return (True, None)
            del self._data["lines"][index]
            self.request.session.modified = True
            return (True, None)

        if index is None:
            # Add to cart if not in there already
            data = {'key': create_key(ctype, pk, options), 'qty': qty,
                    'options': options}
            line = self.make_line_obj(data)
            errors = line.get_errors()
            if errors:
                return (False, errors)

            # Append line if no errors
            self._init_session_cart()
            self._data["lines"].append(data)
        else:
            # Already in the cart, so update the existing line
            data = self._data["lines"][index]
            data['qty'] = qty
            line = self.make_line_obj(data)
            errors = line.get_errors()
            if errors:
                return (False, errors)

            # Update data if no errors
            self._data["lines"][index] = data

        self.request.session.modified = True
        return (True, None)

    def get_line_cls(self):
        """Subclasses should override this if SessionCartLine is also
           subclassed. """
        return SessionCartLine

    def make_line_obj(self, data):
        return self.get_line_cls()(parent_object=self, **data)

    def get_line(self, ctype, pk, options={}):
        index = self._line_index(ctype, pk, options)
        if index is None:
            return None
        return self.make_line_obj(self._data["lines"][index])

    def get_lines(self):
        if self._data is None:
            return
        for line in self._data["lines"]:
            line = self.make_line_obj(line)
            if line.item:
                yield line

    def count(self):
        if self._data is None:
            return 0
        return sum(r['qty'] for r in self._data["lines"])

    @property
    def subtotal(self):
        if self._data is None:
            return decimal.Decimal(0)
        return decimal.Decimal(sum(line.total for line in self.get_lines()))

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

        order_key = self._data.get('order_obj')
        if order_key:
            return get_instance(*order_key.split('|'))

        return None

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

    def _line_index(self, ctype, pk, options):
        """Returns the line index for a given ctype/pk/options, if it's
           already in the cart, or None otherwise."""

        app_label, model = ctype.split('.')
        assert issubclass(
            ContentType.objects.get(
                app_label=app_label, model=model).model_class(),
            ICartItem)

        if self._data is not None:
            for i in range(len(self._data["lines"])):
                if self._data["lines"][i]["key"] == create_key(
                        ctype, pk, options):
                    return i
        return None


def make_uuid():
    return uuid.uuid4()


def get_cart(request):
    """Get the current cart - if the cart app is installed, and user is logged
       in, return a db cart (which may be an unsaved instance). Otherwise,
       return a session cart.

       If there's items in the session_cart, merge them into the db cart.
    """

    session_cart = SessionCart(request)

    if apps.is_installed('cart') and request.user.is_authenticated:

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
