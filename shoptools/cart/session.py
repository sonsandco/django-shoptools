import decimal
import json

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

from .base import ICart, ICartItem, ICartLine, IShippable
from .util import validate_options, get_regions_module
from . import settings as cart_settings


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


class SessionCartLine(dict, ICartLine):
    '''Thin wrapper around dict providing some convenience methods for
       accessing computed information about the line, according to ICartLine.
    '''

    def __init__(self, **kwargs):
        assert sorted(kwargs.keys()) == ['key', 'options', 'parent_object',
                                         'quantity']
        return super(SessionCartLine, self).__init__(**kwargs)

    def __setitem__(self, *args):
        raise Exception("Sorry, SessionCartLine instances are immutable.")

    @property
    def item(self):
        ctype, pk, options = unpack_key(self['key'])
        return get_instance(ctype, pk)

    options = property(lambda s: s['options'])
    quantity = property(lambda s: s['quantity'])
    total = property(lambda s: s.item.cart_line_total(s))
    description = property(lambda s: s.item.cart_description())
    parent_object = property(lambda s: s['parent_object'])


class SessionCart(ICart, IShippable):
    """Default session-saved cart class. To implement multiple "carts" in one
       site using this class, pass a distinct session_key to the constructor
       for each. """

    def __init__(self, request, session_key=None):
        self.request = request
        self.session_key = session_key or cart_settings.DEFAULT_SESSION_KEY
        self._shipping_options = {}
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
        """Get shipping options for this cart, if any. """

        if self._data is None:
            return {}
        return json.loads(self._data.get('shipping', '{}'))

    def update_quantity(self, ctype, pk, quantity=1, add=False, options={}):
        assert isinstance(quantity, int)
        options = validate_options(ctype, pk, options)
        index = self._line_index(ctype, pk, options)

        # quantity may be additive or a straight update
        # TODO kill the add argument. cart.add should do this extra calculation
        if add and index is not None:
            quantity += self._data["lines"][index]['quantity']

        # purge if quantity is zero
        if quantity < 1:
            if index is None:
                # fail silently
                return (True, None)
            del self._data["lines"][index]
            self.request.session.modified = True
            return (True, None)

        if index is None:
            # Add to cart if not in there already
            data = {
                'key': create_key(ctype, pk, options),
                'quantity': quantity,
                'options': options
            }
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
            data['quantity'] = quantity
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
        # TODO consistent ordering
        if self._data is None:
            return
        for line in self._data["lines"]:
            line = self.make_line_obj(line)
            if line.item:
                yield line

    def count(self):
        if self._data is None:
            return 0
        return sum(r['quantity'] for r in self._data["lines"])

    @property
    def currency(self):
        regions_module = get_regions_module()
        if regions_module:
            return regions_module.get_region(self.request).currency
        return cart_settings.DEFAULT_CURRENCY

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