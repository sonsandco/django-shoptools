from django.conf.urls import url
from django.views.generic.base import RedirectView

import cart.views
from . import views

urlpatterns = [
    url(r'^cart$', views.cart, {}, 'checkout_cart'),
    url(r'^$', RedirectView.as_view(url='cart', permanent=True), {}),
    url(r'^checkout$', views.checkout, {}, 'checkout_checkout'),
    url(r'^checkout/(\w+)$', views.checkout, {}, 'checkout_checkout'),
    url(r'^checkout/(\w+)/print$', views.invoice, {}, 'checkout_invoice'),
    url(r'^_emails/(\w+)$', views.preview_emails),
]

# identical to the cart views, but generating a checkout snippet

for action in cart.views.all_actions:
    urlpatterns.append(
        url(r'^%s$' % action, getattr(cart.views, action), {
            'ajax_template': 'checkout/cart_ajax.html',
        }, 'checkout_%s' % action))
