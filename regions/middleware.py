# -*- coding: utf-8 -*-

from django.contrib.gis.geoip2 import GeoIP2
from geoip2.errors import AddressNotFoundError
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from .models import Region


LOCATION_SESSION_KEY = getattr(settings, 'LOCATION_SESSION_KEY',
                               'location_info')


def get_ip(request):
    return request.GET.get('REMOTE_ADDR', request.META.get(
        'HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', None)))


def get_region_id(country_code):
    if country_code:
        try:
            region = Region.objects.get(countries__country=country_code)
        except Region.DoesNotExist:
            pass
        else:
            return region.id

    region = Region.get_default()
    if region:
        return region.id


def get_country_code(request):
    try:
        country = GeoIP2().country(get_ip(request))
    except AddressNotFoundError:
        return None
    return country['country_code']


def get_session(request):
    if LOCATION_SESSION_KEY not in request.session:
        request.session[LOCATION_SESSION_KEY] = {}
    return request.session[LOCATION_SESSION_KEY]


class RegionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """Examine the request to determine (and save) country_code and
           region_id, if not already set.
           Saves the minimum info required to the request (and doesn't hit the
           db unless necessary) because we don't assume that all requests
           require this information. """

        info = get_session(request)

        if not info.get('country_code'):
            info['country_code'] = get_country_code(request)
            request.session.modified = True

        if not info.get('region_id'):
            info['region_id'] = get_region_id(info.get('country_code'))
            request.session.modified = True
