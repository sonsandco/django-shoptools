# -*- coding: utf-8 -*-
import socket

try:
    from django.contrib.gis.geoip2 import GeoIP2
except ImportError:
    GeoIP2 = None
else:
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
    if not GeoIP2:
        return None

    try:
        country = GeoIP2().country(get_ip(request))
    except (AddressNotFoundError, socket.gaierror):
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
    if val is None:
        return None

    try:
        return int(val)
    except ValueError:
        return None


def get_region(request):
    """Get region instance from the session region id. """
    info = get_session(request)
    region_id = get_int(info.get('region_id'))
    if region_id:
        try:
            return Region.objects.get(pk=region_id)
        except Region.DoesNotExist:
            pass
    return Region.get_default()


def get_country(request):
    """Get country instance from the session country code. """
    info = get_session(request)
    country_code = info.get('country_code')
    if country_code:
        try:
            return Country.objects.get(country=country_code)
        except Country.DoesNotExist:
            pass
    return None


def regions_data(request):
    """Get region and country info from the session, as a dict for json
       serialization. """

    data = {}

    region = get_region(request)
    data['region'] = region.as_dict()

    country = get_country(request)
    if country:
        data['country'] = country.as_dict()

    return data
