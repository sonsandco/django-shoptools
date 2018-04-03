# -*- coding: utf-8 -*-

from django.conf.urls import url

from shoptools.cart.util import get_html_snippet
from . import views


# TODO: Non-snippet version here, move snippet version to checkout.urls
urlpatterns = [
    url(r'^_change$', views.change_region, {
        'get_html_snippet': get_html_snippet,
    }, 'regions_change_region'),
]
