from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.get_cart, {}, 'cart_get_cart'),
]

for action in views.all_actions:
    urlpatterns.append(url(r'^%s$' % action, getattr(views, action), {},
                           'cart_%s' % action))
