# -*- coding: utf-8 -*-
from django.conf import settings

from .models import ShippingOption
from regions.util import get_region
from cart.cart import get_cart


SHIPPING_SESSION_KEY = getattr(settings, 'SHIPPING_SESSION_KEY',
                               'shipping_info')


def get_session(request):
    if SHIPPING_SESSION_KEY not in request.session:
        request.session[SHIPPING_SESSION_KEY] = {}
    return request.session[SHIPPING_SESSION_KEY]


# TODO: Violating DRY with region.util. Move this to shared util folder?
def get_int(val):
    try:
        return int(val)
    except ValueError:
        return None


def get_shipping_option(request):
    """Get shipping option instance from the session shipping option id. """
    info = get_session(request)
    shipping_option_id = get_int(info.get('shipping_option_id'))
    if shipping_option_id:
        try:
            return ShippingOption.objects.get(pk=shipping_option_id)
        except ShippingOption.DoesNotExist:
            pass
    region = get_region(request)
    return ShippingOption.get_default(region)


def shipping_data(request):
    """Get shipping option from the session as a dict for json
       serialization. """

    data = {}

    shipping_option = get_shipping_option(request)
    data['shipping_option'] = shipping_option.as_dict(get_cart(request))

    return data
