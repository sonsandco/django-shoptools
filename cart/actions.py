from .cart import unpack_key


def cart_action(required=[]):
    '''If any required params are missing, return False, otherwise perform
       action and return True.'''

    def inner(wrapped_func):
        def action_func(data, cart):
            if not all(data.get(p) for p in required):
                return False

            return wrapped_func(data, cart)

        action_func.__name__ = wrapped_func.__name__
        action_func.__doc__ = wrapped_func.__doc__
        return action_func

    return inner


@cart_action()
def update_cart(data, cart):
    # TODO blow this away? Use line-level endpoints instead

    # remove things if a remove button was clicked
    key_to_remove = data.get('remove', None)
    if key_to_remove:
        cart.remove(*unpack_key(key_to_remove))
    else:
        # otherwise, update quantities
        prefix = "qty:"
        for (name, val) in data.items():
            if name.startswith(prefix):
                key = name[len(prefix):]
                try:
                    qty = int(val)
                except ValueError:
                    pass
                else:
                    cart.update_quantity(*unpack_key(key), qty=qty)
    return True


@cart_action(required=['ctype', 'pk', 'qty'])
def quantity(data, cart):
    try:
        qty = int(data["qty"])
    except ValueError:
        return False
    return cart.update_quantity(data["ctype"], data["pk"], qty)


@cart_action(required=['ctype', 'pk'])
def add(data, cart):
    try:
        qty = int(data.get("qty", 1))
    except ValueError:
        return False
    return cart.add(data["ctype"], data["pk"], qty)


@cart_action(required=['confirm'])
def clear(data, cart):
    confirm = data.get('confirm', None)
    if confirm:
        return cart.clear()

@cart_action()
def set_shipping_options(data, cart):
    # TODO validate POSTed shipping options

    cart.set_shipping_options(data.dict())
    return (True, None)


@cart_action()
def update_vouchers(data, cart):
    codes = map(str.strip, data.get('codes', '').split(','))
    return cart.update_vouchers([c for c in codes if c])
