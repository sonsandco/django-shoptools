from django.conf.urls import url

from . import views


urlpatterns = []

for action in views.all_actions:
    urlpatterns.append(url(r'^%s$' % action, getattr(views, action), {},
                           'favourites_%s' % action))
urlpatterns.append(url(r'^create$', views.create, {},
                       'favourites_create'))

urlpatterns.append(url(r'^$', views.index, {},
                       'favourites_index'))
urlpatterns.append(url(r'^dashboard/$', views.dashboard, {},
                       'favourites_dashboard'))
urlpatterns.append(url(r'^([\w\-]+)$', views.detail, {},
                       'favourites_detail'))
