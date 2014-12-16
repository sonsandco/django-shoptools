from cart.models import Cart
from .shipping import calculate_shipping


def cart(request):
    cart = Cart(request)
    return {
        'cart': cart,
        'shipping_cost': calculate_shipping(cart.rows()),
    }