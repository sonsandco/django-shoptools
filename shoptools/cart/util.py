from django.apps import apps
from django.template.loader import render_to_string

from shoptools.util import \
    get_regions_module, get_shipping_module, get_vouchers_module
from .session import SessionCart


def get_cart(request):
    """Get the current cart - if the cart app is installed, and user is logged
       in, return a db cart (which may be an unsaved instance). Otherwise,
       return a session cart.

       If there's items in the session_cart, merge them into the db cart.
    """
    session_cart = SessionCart(request)

    if apps.is_installed('shoptools.cart') and request.user.is_authenticated:
        # django doesn't like this to be imported at compile-time if the app is
        # not installed
        from .models import SavedCart

        try:
            cart = SavedCart.objects.get(user=request.user)
        except SavedCart.DoesNotExist:
            cart = SavedCart(user=request.user)

        cart.set_request(request)

        # merge session cart, if it exists
        if session_cart.count():
            if not cart.pk:
                cart.save()
            session_cart.save_to(cart)
            session_cart.clear()
        return cart

    return session_cart


def get_html_snippet(request, cart=None, errors=[]):
    """
    Both the cart and the checkout app have a get_html_snippet function.

    This (cart version) is intended to return a minimal snippet containing only
    the cart rows, so that it can be used to populate a cart summary panel, for
    example.
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

    return render_to_string('cart/html_snippet.html', ctx, request=request)
