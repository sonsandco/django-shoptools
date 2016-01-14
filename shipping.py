from cart.cart import ICart


def calculate_shipping(cart):
    '''Return shipping cost for the given cart, which may be a session cart or
       or a db-saved order.'''

    assert isinstance(cart, ICart)

    return 0
