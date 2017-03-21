# -*- coding: utf-8 -*-

from django.contrib.gis.geoip2 import GeoIP2
from geoip2.errors import AddressNotFoundError
from django.conf import settings

from .models import Region, Country


LOCATION_SESSION_KEY = getattr(settings, 'LOCATION_SESSION_KEY',
                               'location_info')


def get_ip(request):
    return request.GET.get('REMOTE_ADDR', request.META.get(
        'HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', None)))


def get_region_id(country_code=None):
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


def update_session(request):
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


def get_int(val):
    try:
        return int(val)
    except ValueError:
        return None


def regions_data(request):
    """Get region info from the session, as a dict. Assumes session values
       are valid, because they should be validated before they're set"""

    data = {}
    info = get_session(request)

    region_id = get_int(info.get('region_id'))
    if region_id:
        region = Region.objects.get(pk=region_id)
        data['region'] = region.as_dict()

    country_code = info.get('country_code')
    if country_code:
        country = Country.objects.get(country=country_code)
        data['region'] = country.as_dict()

    return data
