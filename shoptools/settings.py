# -*- coding: utf-8 -*-

from django.conf import settings


ACCOUNTS_MODULE = getattr(settings, 'SHOPTOOLS_ACCOUNTS_MODULE', None)
REGIONS_MODULE = getattr(settings, 'SHOPTOOLS_REGIONS_MODULE', None)
SHIPPING_MODULE = getattr(settings, 'SHOPTOOLS_SHIPPING_MODULE', None)
VOUCHERS_MODULE = getattr(settings, 'SHOPTOOLS_VOUCHERS_MODULE', None)
FAVOURITES_MODULE = getattr(settings, 'SHOPTOOLS_FAVOURITES_MODULE', None)
PAYMENT_MODULE = getattr(settings, 'SHOPTOOLS_PAYMENT_MODULE', None)

DEFAULT_SESSION_KEY = getattr(settings, 'CART_DEFAULT_SESSION_KEY', 'cart')

FAVOURITES_SESSION_KEY = getattr(settings, 'FAVOURITES_SESSION_KEY',
                                 'favourites_info')
FAVOURITES_SESSION_POST_KEY = getattr(settings, 'FAVOURITES_SESSION_POST_KEY',
                                      'favourites_post')

LOCATION_COOKIE_NAME = getattr(settings, 'LOCATION_COOKIE_NAME',
                               'shoptools_location')

DEFAULT_CURRENCY_CODE = getattr(settings, 'DEFAULT_CURRENCY_CODE', 'NZD')
DEFAULT_CURRENCY_SYMBOL = getattr(settings, 'DEFAULT_CURRENCY_SYMBOL', '$')
