# -*- coding: utf-8 -*-
import socket
import json

try:
    from django.contrib.gis.geoip2 import GeoIP2
except ImportError:
    GeoIP2 = None
else:
    from geoip2.errors import AddressNotFoundError

from shoptools import settings as shoptools_settings
from .models import Region, Country
from .forms import RegionSelectionForm


COOKIE_MAX_AGE = 52*7*24*60*60  # 1 year


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
    except (AddressNotFoundError, socket.gaierror, UnicodeError):
        # Extra long IP addresses (ie. incorrect ones) can generate a
        # UnicodeError within GeoIP in some versions of Python.
        return None
    return country['country_code']


def get_cookie(request):
    if shoptools_settings.LOCATION_COOKIE_NAME not in request.COOKIES:
        return {}
    info = json.loads(request.COOKIES[shoptools_settings.LOCATION_COOKIE_NAME])
    return info


def set_cookie(request, response, info):
    info = json.dumps(info)
    response.set_cookie(shoptools_settings.LOCATION_COOKIE_NAME, info,
                        max_age=COOKIE_MAX_AGE, httponly=False)
    request.COOKIES[shoptools_settings.LOCATION_COOKIE_NAME] = info


def get_int(val):
    if val is None:
        return None

    try:
        return int(val)
    except ValueError:
        return None


def available_regions(request):
    return [(r.id, r.option_text) for r in Region.objects.all()]


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
    region_id = get_int(region_id)
    if not region_id:
        return False

    info = get_cookie(request)

    if region_id and Region.objects.filter(id=region_id):
        info["region_id"] = region_id
        set_cookie(request, response, info)
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
        info["country_code"] = country_code
        set_cookie(request, response, info)
        return True
    else:
        return False


def regions_context(request):
    """Return region related context for use in cart related html.
    """
    valid_regions = list(available_regions(request))
    selected_region = get_region(request)

    initial = {
        'region_id': selected_region.id
    }

    if valid_regions:
        if selected_region.id not in [r_id for (r_id, name) in valid_regions]:
            # prepend a blank one if the current option is invalid
            valid_regions = (('', 'Select region'), ) + \
                tuple(valid_regions)
            initial = {}

        region_selection_form = RegionSelectionForm(
            initial=initial,
            region_choices=valid_regions)
    else:
        region_selection_form = None

    return {
        'available_regions': valid_regions,
        'selected_region': selected_region,
        'region_selection_form': region_selection_form
    }


def regions_data(request):
    """Get region and country info from the session, as a dict for json
       serialization. """
    valid_regions = list(available_regions(request))
    selected_region = get_region(request)

    if not (valid_regions and selected_region):
        return None

    return {
        'available_regions': valid_regions,
        'selected_region': selected_region.as_dict(),
    }
