# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^orders', views.orders, {}, 'accounts_orders'),
    url(r'^create', views.create, {}, 'accounts_create'),
    url(r'^details', views.details, {}, 'accounts_details'),
]
