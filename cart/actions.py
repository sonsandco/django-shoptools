

def cart_action(required=[]):
    '''If any required params are missing, return False, otherwise perform
       action and return True.'''

    def inner(wrapped_func):
        def view_func(request, cart):
            if not all(request.POST.get(p) for p in required):
                return False

            wrapped_func(request, cart)
            return True

        view_func.__name__ = wrapped_func.__name__
        view_func.__doc__ = wrapped_func.__doc__
        return view_func

    return inner


@cart_action()
def update_cart(request, cart):
    # remove things if a remove button was clicked
    key_to_remove = request.POST.get('remove', None)
    if key_to_remove:
        cart.remove(*cart.unpack_key(key_to_remove))
    else: 
        # otherwise, update quantities
        prefix = "qty:"
        for (name, val) in request.POST.items():
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
        for (name, val) in request.POST.items():
            if name.startswith(prefix):
                key, option = name[len(prefix):].split(':')
                cart.update_options(*cart.unpack_key(key), **{option: val})


@cart_action(required=['ctype', 'pk'])
def add(request, cart):
    ctype = request.POST["ctype"]
    pk = request.POST["pk"]
    qty = request.POST.get("qty", 1)
    cart.add(ctype, pk, qty)


@cart_action(required=['ctype', 'pk'])
def remove(request, cart):
    ctype = request.POST["ctype"]
    pk = request.POST["pk"]
    cart.remove(ctype, pk)


@cart_action(required=['confirm'])
def clear(request, cart):
    confirm = request.POST.get('confirm', None)
    if confirm:
        cart.clear()

