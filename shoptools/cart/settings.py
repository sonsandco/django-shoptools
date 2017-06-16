# -*- coding: utf-8 -*-

from django.conf import settings


SHIPPING_MODULE = getattr(settings, 'CART_SHIPPING_MODULE', None)
VOUCHERS_MODULE = getattr(settings, 'CART_VOUCHERS_MODULE', None)
ACCOUNTS_MODULE = getattr(settings, 'CART_ACCOUNTS_MODULE', None)

DEFAULT_SESSION_KEY = getattr(settings, 'CART_DEFAULT_SESSION_KEY', 'cart')
DEFAULT_CURRENCY = getattr(settings, 'DEFAULT_CURRENCY', 'NZD')
# CURRENCY_COOKIE_NAME = getattr(settings, 'CURRENCY_COOKIE_NAME', None)
