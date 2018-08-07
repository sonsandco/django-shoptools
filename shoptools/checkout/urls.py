from django.conf.urls import url
from django.views.generic.base import RedirectView

import shoptools.cart.views
from .util import get_html_snippet
from . import views


urlpatterns = [
    url(r'^cart$', views.cart, {}, 'checkout_cart'),
    url(r'^$', RedirectView.as_view(url='cart', permanent=True), {}),
    url(r'^checkout$', views.checkout, {}, 'checkout_checkout'),
    url(r'^checkout/([\w\-]+)$', views.checkout, {}, 'checkout_checkout'),
    url(r'^checkout/([\w\-]+)/print$', views.invoice, {}, 'checkout_invoice'),
    url(r'^_emails/([\w\-]+)$', views.preview_emails),
    url(r'^_emails/$', views.preview_first_emails),
]

# identical to the cart views, but generating a checkout snippet
for action in shoptools.cart.views.all_actions:
    urlpatterns.append(
        url(r'^_action/%s$' % action, getattr(shoptools.cart.views, action), {
            'get_html_snippet': get_html_snippet,
        }, name='checkout_%s' % action))
