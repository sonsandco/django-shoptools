from django.conf.urls import url

from .views import cart, checkout, success

urlpatterns = (
    url(r'^cart$', cart, {}, 'checkout_cart'),
    url(r'^$', checkout, {}, 'checkout_checkout'),
    url(r'^(\w+)$', checkout, {}, 'checkout_checkout'),
    url(r'^(\w+)/success$', success, {}, 'checkout_success'),
)
