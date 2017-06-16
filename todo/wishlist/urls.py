from django.conf.urls import url

import shoptools.cart.views
from . import views
from .models import get_wishlist

urlpatterns = (
    # url(r'^_quantity$', views.quantity, {}, 'wishlist_quantity'),
    url(r'^_quantity$', cart.views.quantity, {
        'ajax_template': None,
        'get_cart': get_wishlist,
    }, 'wishlist_quantity'),

    url(r'^$', views.wishlist, {}, 'wishlist_wishlist'),
    url(r'^(\w+)$', views.wishlist, {}, 'wishlist_wishlist'),
)
