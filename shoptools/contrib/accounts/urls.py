# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^orders$', views.orders, {}, 'accounts_orders'),
    url(r'^create$', views.create, {}, 'accounts_create'),
    url(r'^create_user$', views.create_user, {}, 'accounts_create_user'),
    url(r'^details$', views.details, {}, 'accounts_details'),
]
