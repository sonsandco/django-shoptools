# -*- coding: utf-8 -*-
"""
Basic example shipping module which delegates the shipping calculation to the
product's get_shipping_cost method, and restricts shipping destination to
countries within the current region.
"""


from regions.util import get_region
from .util import get_shipping_option


def get_errors(cart):
    """Return a list of error strings, or an empty list if valid. """

    return []


def calculate(cart):
    """Return the total shipping cost for the cart. """

    shipping_option = get_shipping_option(cart.request)
    return shipping_option.get_cost(cart)


def available_countries(cart):
    """Return iterable of country choices which this cart could be shipped to.
       Choices should be of the form (country_code, country_name)
       Return None if there's no restriction. """

    region = get_region(cart.request)
    return ((c.country.code, c.country.name) for c in region.countries.all())


def available_options(cart):
    """Return iterable of shipping option choices applicable to this cart.
       Choices should be of the form (shipping_option_id, shipping_option_name)
       Return None if there's no valid options. """

    region = get_region(cart.request)
    return ((o.id, o.name) for o in region.shipping_options.all())
