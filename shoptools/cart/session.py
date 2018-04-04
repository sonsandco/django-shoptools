import decimal
import json

from shoptools.abstractions.models import \
    ICart, ICartItem, ICartLine, IShippable
from shoptools.util import \
    validate_options, get_regions_module, create_instance_key, \
    unpack_instance_key
from shoptools import settings as shoptools_settings


KEY_SEPARATOR = '|'


def create_line_key(instance, options):
    """Create a unique (string) key for a model instance and optional options
       dict. """

    instance_key = create_instance_key(instance)
    options = json.dumps(validate_options(instance, options), sort_keys=True)

    return KEY_SEPARATOR.join(map(str, instance_key + (options, )))


def unpack_line_key(key):
    """Retrieve a model instance and options dict from a unique key created by
       create_line_key. """

    bits = key.split(KEY_SEPARATOR)

    instance = unpack_instance_key(*bits[:-1])
    options = json.loads(bits[-1])

    return (instance, options)


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
        instance, options = unpack_line_key(self.key)
        return instance

    options = property(lambda s: s['options'])
    quantity = property(lambda s: s['quantity'])
    total = property(lambda s: s.item.cart_line_total(s))
    description = property(lambda s: s.item.cart_description())
    parent_object = property(lambda s: s['parent_object'])
    key = property(lambda s: s['key'])


class SessionCart(ICart, IShippable):
    """Default session-saved cart class. To implement multiple "carts" in one
       site using this class, pass a distinct session_key to the constructor
       for each. """

    def __init__(self, request, session_key=None):
        self.request = request
        self.session_key = \
            session_key or shoptools_settings.DEFAULT_SESSION_KEY
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

    def set_shipping_option(self, option_id):
        """Saves the provided option_id to this SessionCart."""

        self._init_session_cart()
        self._data['shipping_option'] = option_id
        self.request.session.modified = True

    def get_shipping_option(self):
        """Get shipping options for this cart, if any. """

        if self._data is None:
            return None
        return self._data.get('shipping_option', None)

    def update_quantity(self, instance, quantity=1, add=False, options={}):
        assert isinstance(quantity, int)
        options = validate_options(instance, options)
        index = self._line_index(instance, options)

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
                'key': create_line_key(instance, options),
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

    def update_options(self, key, options):
        # TODO make this less convoluted
        instance, old_options = unpack_line_key(key)
        old_options = validate_options(instance, old_options)
        old_index = self._line_index(instance, old_options)

        if old_index is None:
            return (False, ['Invalid options'])

        # Create new cart line
        old_line = self.get_line(instance, old_options)
        new_options = validate_options(instance, options)
        new_data = {
            'key': create_line_key(instance, new_options),
            'quantity': old_line.quantity,
            'options': new_options
        }
        new_line = self.make_line_obj(new_data)
        errors = new_line.get_errors()
        if errors:
            return (False, errors)

        # Swap out lines if no errors
        self._data["lines"].append(new_data)
        del self._data["lines"][old_index]

        self.request.session.modified = True
        return (True, None)

    def get_line_cls(self):
        """Subclasses should override this if SessionCartLine is also
           subclassed. """
        return SessionCartLine

    def make_line_obj(self, data):
        return self.get_line_cls()(parent_object=self, **data)

    def get_line(self, instance, options={}):
        index = self._line_index(instance, options)
        if index is None:
            return None
        return self.make_line_obj(self._data["lines"][index])

    def get_lines(self):
        # TODO consistent ordering
        if self._data is None:
            return
        rv = []
        for line in self._data["lines"]:
            line = self.make_line_obj(line)
            if line.item:
                rv.append(line)
        return rv

    def count(self):
        if self._data is None:
            return 0
        return sum(r['quantity'] for r in self._data["lines"])

    def get_currency(self):
        regions_module = get_regions_module()
        if regions_module:
            selected_region = regions_module.get_region(self.request)
            if selected_region and selected_region.currency:
                return (selected_region.currency.code,
                        selected_region.currency.symbol)
        return (shoptools_settings.DEFAULT_CURRENCY_CODE,
                shoptools_settings.DEFAULT_CURRENCY_SYMBOL)

    @property
    def subtotal(self):
        if self._data is None:
            return decimal.Decimal(0)
        return decimal.Decimal(
            sum(line.total if line.total else 0 for line in self.get_lines()))

    @property
    def total(self):
        return self.subtotal + self.shipping_cost - self.total_discount

    def set_order_obj(self, obj):
        self._data['order_obj'] = create_instance_key(obj)
        self.request.session.modified = True

    def get_order_obj(self):
        if self._data is None:
            return None

        order_key = self._data.get('order_obj')
        if order_key:
            return unpack_instance_key(*order_key)

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

    def _line_index(self, instance, options):
        """Returns the line index for a given ctype/pk/options, if it's
           already in the cart, or None otherwise."""

        assert isinstance(instance, ICartItem)

        if self._data is not None:
            for i in range(len(self._data["lines"])):
                key = create_line_key(instance, options)
                if self._data["lines"][i]["key"] == key:
                    return i
        return None
