# -*- coding: utf-8 -*-
"""
Basic example shipping module which delegates the shipping calculation to the
product's get_shipping_cost method, and restricts shipping destination to
countries within the current region.
"""

from django.db.models import Q

from shoptools.contrib.regions.util import get_region
from .models import Option, ShippingOption


def available_countries(cart):
    """Return iterable of country choices which this cart could be shipped to.
       Choices should be of the form (country_code, country_name)
    """

    region = get_region(cart.request)
    return ((c.country.code, c.country.name) for c in region.countries.all())


def available_options_qs(cart):
    """Return available Options for this cart """

    region = get_region(cart.request)

    region_query = Q(shipping_options__region=region)
    min_query = Q(shipping_options__min_cart_value__lte=cart.subtotal)
    max_query = \
        Q(shipping_options__max_cart_value__isnull=True) | \
        Q(shipping_options__max_cart_value__gte=cart.subtotal)

    return Option.objects.filter(region_query, min_query, max_query).distinct()


def available_options(cart):
    """Return iterable of shipping option choices applicable to this cart.
       Choices should be of the form
       (shipping_option_slug, shipping_option_name)
    """

    return available_options_qs(cart).values_list('slug', 'name')


def calculate(cart):
    """Return the total shipping cost for the cart. """

    if not hasattr(cart, 'get_shipping_option'):
        raise NotImplementedError()
    option_slug = cart.get_shipping_option()
    region = get_region(cart.request)

    region_query = Q(region=region)
    min_query = Q(min_cart_value__lte=cart.subtotal)
    max_query = Q(max_cart_value__isnull=True) | \
        Q(max_cart_value__gte=cart.subtotal)

    options = ShippingOption.objects.filter(
        region_query, min_query, max_query
    ).filter(option__slug=option_slug)
    option = options.order_by('cost').first()

    # assume there will be options available
    if option:
        return option.cost

    return 0
