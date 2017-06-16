# -*- coding: utf-8 -*-

from django.contrib.gis.geoip2 import GeoIP2

from shoptools.cart import get_cart
from .models import Region, Country
from .settings import COUNTRY_COOKIE_NAME
from .api import save_to_cart


def get_ip(request):
    return request.GET.get('REMOTE_ADDR', request.META.get(
        'HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', None)))


class CountryMiddleware(object):
    def process_request(self, request):
        '''Examine the request to determine (and save) country, if not
           already set. '''

        cart = get_cart(request)

        if not cart.get_shipping_options().get('country', None):
            code = request.COOKIES.get(COUNTRY_COOKIE_NAME)

            if not code:
                try:
                    code = GeoIP2().country(get_ip(request))['country_code']
                # upon failure for any reason, simply pass so we use our
                # default region / country
                except:
                    pass

            country = None
            try:
                country = Country.objects.get(code=code)
            except Country.DoesNotExist:
                region = Region.get_default()
                if region:
                    country = region.get_default_country()

            if country:
                save_to_cart(cart, country=country.code)
