from .models import Cart


def cart_action(required=[]):
    '''If any required params are missing, return False, otherwise perform
       action and return True.'''

    def inner(wrapped_func):
        def action_func(data, cart=None, request=None):
            assert cart or request
            
            if not cart:
                cart = Cart(request)
            
            if not all(data.get(p) for p in required):
                return False

            return wrapped_func(data, cart)

        action_func.__name__ = wrapped_func.__name__
        action_func.__doc__ = wrapped_func.__doc__
        return action_func

    return inner


@cart_action()
def update_cart(data, cart):
    # remove things if a remove button was clicked
    key_to_remove = data.get('remove', None)
    if key_to_remove:
        cart.remove(*cart.unpack_key(key_to_remove))
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
                    cart.update_quantity(*cart.unpack_key(key), qty=qty)
        
        # and options
        prefix = "option:"
        for (name, val) in data.items():
            if name.startswith(prefix):
                key, option = name[len(prefix):].split(':')
                cart.update_options(*cart.unpack_key(key), **{option: val})
    
    return True

@cart_action(required=['ctype', 'pk'])
def add(data, cart):
    ctype = data["ctype"]
    pk = data["pk"]
    qty = data.get("qty", 1)
    return cart.add(ctype, pk, qty)
    

@cart_action(required=['ctype', 'pk'])
def remove(data, cart):
    ctype = data["ctype"]
    pk = data["pk"]
    return cart.remove(ctype, pk)


@cart_action(required=['confirm'])
def clear(data, cart):
    confirm = data.get('confirm', None)
    if confirm:
        return cart.clear()


@cart_action()
def update_shipping(data, cart):
    return cart.update_shipping(data.dict())
