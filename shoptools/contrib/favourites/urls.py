from django.conf.urls import url

from . import views


urlpatterns = []

for action in views.all_actions:
    urlpatterns.append(url(r'^%s$' % action, getattr(views, action), {},
                           'favourites_%s' % action))


urlpatterns.append(url(r'^$', views.favourites, {}, 'favourites_favourites'))
urlpatterns.append(url(r'^([\w\-]+)$', views.favourites, {},
                       'favourites_favourites'))
