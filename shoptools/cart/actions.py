from .util import unpack_instance_key


def cart_action(params=[]):
    """Check for required params and perform action if valid.
       Return in the format

           (success, errors)

       where success is True if the action was performed successfully, False
       if there were errors (i.e. an item is sold out), or None if the request
       is invalid, (i.e. missing a required parameter)

       params is a list of tuples of the form (field, cast_func, required)
    """

    def inner(wrapped_func):
        def action_func(data, cart):
            errors = []
            kwargs = dict(data)

            for field, cast, required in params:
                val = data.get(field)

                if required and not val:
                    errors.append('%s is required' % field)

                if val:
                    try:
                        kwargs[field] = cast(val)
                    except ValueError:
                        errors.append('%s is invalid' % field)

            if len(errors):
                return (False, errors)

            return wrapped_func(cart, **kwargs)

        action_func.__name__ = wrapped_func.__name__
        action_func.__doc__ = wrapped_func.__doc__
        return action_func

    return inner


@cart_action(params=(
    ('ctype', str, True),
    ('pk', str, True),
    ('quantity', int, True),
))
def quantity(cart, ctype, pk, quantity, **options):
    """Update an item's quantity in the cart. """

    instance = unpack_instance_key(ctype, pk)
    return cart.update_quantity(instance, quantity, options=options)


@cart_action(params=(
    ('ctype', str, True),
    ('pk', str, True),
    ('quantity', int, False),
))
def add(cart, ctype, pk, quantity=None, **options):
    """Add an item to the cart. """

    instance = unpack_instance_key(ctype, pk)
    return cart.add(instance, quantity, options=options)


@cart_action(params=(
    ('confirm', str, True),
))
def clear(cart, data):
    """Remove everything from the cart. """

    confirm = data.get('confirm', None)
    if confirm:
        cart.clear()
    return (True, None)


@cart_action()
def set_shipping_options(cart, data):
    """Set shipping options for a cart. No validation here - invalid options
       will just be ignored, and any errors will be displayed on the cart
       page. """

    cart.set_shipping_options(data.dict())
    return (True, None)


@cart_action()
def set_voucher_codes(cart, data):
    """Set voucher codes for a cart. No validation here - invalid codes
       will just be ignored, with an error message displayed on the cart
       page. """

    codes = map(str.strip, data.get('codes', '').split(','))
    cart.set_voucher_codes([c for c in codes if c])
    return (True, None)
