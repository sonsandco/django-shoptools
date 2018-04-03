from django.template.loader import render_to_string

from shoptools.util import get_regions_module, get_shipping_module
from shoptools.cart import get_cart


def get_html_snippet(request, cart=None):
    if not cart:
        cart = get_cart(request)
    errors = cart.get_errors()

    ctx = {
        'cart': cart,
        'cart_errors': errors
    }

    region_module = get_regions_module()
    if region_module:
        ctx.update(region_module.get_context(request))

    shipping_module = get_shipping_module()
    if shipping_module:
        ctx.update(shipping_module.get_context(cart))

    return render_to_string('checkout/cart_ajax.html', ctx, request=request)
