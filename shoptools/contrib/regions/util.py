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


# Use a cookie separate from the session, so we can vary the cache based on
# region
LOCATION_INFO_COOKIE = getattr(settings, 'SHOPTOOLS_LOCATION_COOKIE',
                               'shoptools_location')


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


def get_cookie(request):
    if LOCATION_INFO_COOKIE not in request.COOKIES:
        return {}
    return request.COOKIES[LOCATION_INFO_COOKIE]


def get_int(val):
    if val is None:
        return None

    try:
        return int(val)
    except ValueError:
        return None


def regions(request):
    return ((r.id, r.name) for r in Region.objects.all())


def get_region(request):
    """Get region instance from the session region id. """
    info = get_cookie(request)
    region_id = get_int(info.get('region_id'))
    if region_id:
        try:
            return Region.objects.get(id=region_id)
        except Region.DoesNotExist:
            pass
    return Region.get_default()


def set_region(request, response, region_id):
    """Set region instance."""
    info = get_cookie(request)

    if region_id and Region.objects.filter(id=region_id):
        info['region_id'] = region_id
        response.set_cookie(LOCATION_INFO_COOKIE, info)
        request.COOKIES[LOCATION_INFO_COOKIE] = info
        return True
    else:
        return False


def get_country(request, response):
    """Get country instance from the session country code. """
    info = get_cookie(request)
    country_code = info.get('country_code')
    if country_code:
        try:
            return Country.objects.get(country=country_code)
        except Country.DoesNotExist:
            pass
    return None


def set_country(request, response, country_code):
    """Set region instance."""
    info = get_cookie(request)

    if country_code and Country.objects.filter(country=country_code):
        info['country_code'] = country_code
        response.set_cookie(LOCATION_INFO_COOKIE, info)
        request.COOKIES[LOCATION_INFO_COOKIE] = info
        return True
    else:
        return False


def regions_data(request):
    """Get region and country info from the session, as a dict for json
       serialization. """

    data = {}

    region = get_region(request)
    if region:
        data['region'] = region.as_dict()

    country = get_country(request)
    if country:
        data['country'] = country.as_dict()

    return data
