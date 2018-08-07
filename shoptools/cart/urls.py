from django.conf.urls import url

from . import views
from .util import get_html_snippet


urlpatterns = [
    url(r'^$', views.get_cart, {}, 'cart_get_cart'),
]

for action in views.all_actions:
    urlpatterns.append(url(r'^%s$' % action, getattr(views, action), {
        'get_html_snippet': get_html_snippet,
    }, name='cart_%s' % action))
