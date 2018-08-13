from django.template.loader import render_to_string

from shoptools.util import \
    get_regions_module, get_shipping_module, get_vouchers_module
from shoptools.cart.util import get_cart


def get_html_snippet(request, cart=None, errors=[]):
    """
    Both the cart and the checkout app have a get_html_snippet function.

    This (checkout version) is intended to return a snippet containing all
    information that may need to be updated when the user takes an action on
    the cart page (eg. cart rows, region and shipping selects, cart totals).
    """
    if not cart:
        cart = get_cart(request)

    if not errors:
        errors = cart.get_errors()

    ctx = {
        'cart': cart,
        'cart_errors': errors
    }

    region_module = get_regions_module()
    if region_module:
        context = region_module.get_context(request)
        if context:
            ctx.update(context)

    shipping_module = get_shipping_module()
    if shipping_module:
        context = shipping_module.get_context(cart)
        if context:
            ctx.update(context)

    vouchers_module = get_vouchers_module()
    if vouchers_module:
        context = vouchers_module.get_context(cart)
        if context:
            ctx.update(context)

    return render_to_string('checkout/snippets/html_snippet.html', ctx,
                            request=request)
