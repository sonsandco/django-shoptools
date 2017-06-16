# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^_option$', views.change_option, {}, 'shipping_change_option'),
    url(r'^_country$', views.change_country, {}, 'shipping_change_country'),
    url(r'^_region$', views.change_region, {}, 'shipping_change_region'),
]
