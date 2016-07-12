from cart.cart import ICart


def calculate_shipping(cart):
    """Return shipping cost for the given cart, which may be a session cart or
       or a db-saved order. The cart.shipping_options will contain the result
       of get_session(request) (or the saved shipping options if it's an
       order). """

    assert isinstance(cart, ICart)

    return 0


def get_session(request):
    """Return a dict of shipping options, stored in the session. """

    return {}
