from django.conf.urls import url

from .views import get_cart, update_cart, add, remove, clear, update_shipping

urlpatterns = (
    url(r'^$', get_cart, {}, 'cart_get_cart'),
    url(r'^update/$', update_cart, {}, 'cart_update_cart'),
    url(r'^add/$', add, {}, 'cart_add'),
    url(r'^remove/$', remove, {}, 'cart_remove'),
    url(r'^clear/$', clear, {}, 'cart_clear'),
    url(r'^shipping/$', update_shipping, {}, 'cart_update_shipping'),
)
