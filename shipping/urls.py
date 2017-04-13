# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^option$', views.change_shipping_option, {},
        'shipping_change_option'),
]
