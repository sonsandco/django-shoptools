

def cart_action(required=[]):
    """Check for required params and perform action if valid.
       Return in the format

           (success, errors)

       where success is True if the action was performed successfully, False
       if there were errors (i.e. an item is sold out), or None if the request
       is invalid, (i.e. missing a required parameter)
    """

    def inner(wrapped_func):
        def action_func(data, cart):
            if not all(data.get(p) for p in required):
                return (None, 'Missing required info')

            return wrapped_func(data, cart)

        action_func.__name__ = wrapped_func.__name__
        action_func.__doc__ = wrapped_func.__doc__
        return action_func

    return inner


@cart_action(required=['ctype', 'pk', 'quantity'])
def quantity(data, cart):
    try:
        quantity = int(data['quantity'])
    except ValueError:
        return False
    # TODO separate validation - cart methods to assume valid data

    # TODO fix
    options = dict(data)
    del options['ctype']
    del options['pk']
    del options['quantity']

    return cart.update_quantity(
        data['ctype'], data['pk'], quantity, options=options)


@cart_action(required=['ctype', 'pk'])
def add(data, cart):
    try:
        quantity = int(data.get("quantity", 1))
    except ValueError:
        return (False, 'Invalid quantity')
    # TODO separate validation - cart methods to assume valid data
    # cart.add should take an instance, not ctype and pk
    # a separate layer should validate and convert these to an instance,
    # and grab relevant options. For now just pass the whole POST as options,
    # it'll ignore anything invalid

    # TODO fix
    options = dict(data)
    del options['ctype']
    del options['pk']

    return cart.add(data["ctype"], data["pk"], quantity, options=options)


@cart_action(required=['confirm'])
def clear(data, cart):
    confirm = data.get('confirm', None)
    if confirm:
        cart.clear()
    return (True, None)


@cart_action()
def set_shipping_options(data, cart):
    # TODO validate POSTed shipping options

    cart.set_shipping_options(data.dict())
    return (True, None)


@cart_action()
def set_voucher_codes(data, cart):
    codes = map(str.strip, data.get('codes', '').split(','))
    cart.set_voucher_codes([c for c in codes if c])
    return (True, None)
