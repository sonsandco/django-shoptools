# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^orders', views.orders, {}, 'accounts_orders'),
    url(r'^history', views.history, {}, 'accounts_history'),
    url(r'^details', views.details, {}, 'accounts_details'),
    url(r'^recent', views.recent, {}, 'accounts_recent'),

    url(r'^_data$', views.account_data_view, {}, 'accounts_account_data'),
]
