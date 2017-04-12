from datetime import datetime

from django.db import models
from django.conf import settings

from cart.cart import BaseOrder, BaseOrderLine, SessionCart, make_uuid


WISHLIST_SESSION_KEY = getattr(settings, 'WISHLIST_SESSION_KEY', 'wishlist')


def get_wishlist(request):
    session_wishlist = SessionCart(request, WISHLIST_SESSION_KEY)

    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.get(user=request.user)
        except Wishlist.DoesNotExist:
            wishlist = Wishlist(user=request.user)

        # merge session wishlist, if it exists
        if session_wishlist.count():
            if not wishlist.pk:
                wishlist.save()
            session_wishlist.save_to(wishlist)
            session_wishlist.clear()

        return wishlist
    else:
        return session_wishlist


class Wishlist(BaseOrder):
    """This model is used interchangeably with cart.cart.SessionCart, so it
       implements many of the same methods. """

    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    secret = models.UUIDField(editable=False, default=make_uuid, db_index=True)

    @models.permalink
    def get_absolute_url(self):
        return ('wishlist_wishlist', (self.secret, ))

    def __str__(self):
        return "Wishlist by %s" % self.user.get_full_name()

    # BaseOrder integration
    def get_line_cls(self):
        return WishlistLine


class WishlistLine(BaseOrderLine):
    parent_object = models.ForeignKey(Wishlist)
