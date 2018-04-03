from shoptools.util import unpack_instance_key
from shoptools.cart.actions import cart_action, add, quantity, options, clear


@cart_action(params=(
    ('ctype', str, True),
    ('pk', str, True),
))
def toggle(cart, ctype, pk, **opts):
    instance = unpack_instance_key(ctype, pk)

    if cart.get_line(instance, options=opts):
        return cart.remove(instance, options=opts)
    else:
        return cart.add(instance, 1, options=opts)
