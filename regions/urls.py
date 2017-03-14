# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views


urlpatterns = [
    # url(r'^country$', views.change_country, {}, 'regions_change_country'),
    url(r'^region$', views.change_region, {}, 'regions_change_region'),
]
