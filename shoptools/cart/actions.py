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

            # TODO review this. Should probably be explicit about what's
            # expected. Would need to change how options are passed in though.
            if 'csrfmiddlewaretoken' in kwargs:
                del kwargs['csrfmiddlewaretoken']

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


@cart_action()
def clear(cart, confirm):
    """Remove everything from the cart. """

    cart.clear()
    return (True, None)


@cart_action(params=(
    ('option_slug', str, True),
))
def set_shipping_option(cart, option_slug):
    """Set shipping option id for a cart. No validation here - any errors will
       be displayed on the cart page."""

    cart.set_shipping_option(option_slug)
    return (True, None)


@cart_action(params=(
    ('codes', str, True),
))
def set_voucher_codes(cart, codes):
    """Set voucher codes for a cart. No validation here - invalid codes
       will just be ignored, with an error message displayed on the cart
       page. """

    codes = [c for c in map(str.strip, codes.split(',')) if c]
    cart.set_voucher_codes(codes)
    return (True, None)
