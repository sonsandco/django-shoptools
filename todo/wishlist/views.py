from django.shortcuts import get_object_or_404, redirect
from django.db import models

from utilities.render import render

# import shoptools.cart.actions
# from shoptools.cart.views import cart_view
from .models import Wishlist, get_wishlist


@render('wishlist/wishlist.html')
def wishlist(request, secret=None):
    if secret:
        wishlist = get_object_or_404(Wishlist, secret=secret)
    else:
        wishlist = get_wishlist(request)

    if isinstance(wishlist, models.Model) and getattr(wishlist, 'pk') and \
       wishlist.get_absolute_url() != request.path_info:
        return redirect(wishlist)

    return {
        "wishlist": wishlist,
    }


# quantity = cart_view(cart.actions.quantity, get_cart=get_wishlist,
#                      ajax_template=None)
