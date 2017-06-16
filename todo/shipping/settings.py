# -*- coding: utf-8 -*-

from django.conf import settings

COUNTRY_COOKIE_NAME = getattr(settings,
                              'SHIPPING_COUNTRY_COOKIE_NAME',
                              'shipping')
DEFAULT_CURRENCY = getattr(settings, 'DEFAULT_CURRENCY', 'NZD')
