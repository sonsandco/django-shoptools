# -*- coding: utf-8 -*-
"""
Basic example shipping module which delegates the shipping calculation to the
product's get_shipping_cost method, and restricts shipping destination to
countries within the current region.
"""

from shoptools.util import get_regions_module


regions_module = get_regions_module()


def calculate(cart):
    """Return the total shipping cost for the cart. """

    if cart.subtotal > 200:
        return 0

    return 30


def available_countries(cart):
    """Return iterable of country choices which this cart could be shipped to.
       Choices should be of the form (country_code, country_name)
       Return None if there's no restriction. """

    region = regions_module.get_region(cart.request)
    return [(c.country.code, c.country.name) for c in region.countries.all()]


def available_options(cart):
    """Return the shipping options as a list of two-tuples, suitable for use by
       a django forms ChoiceField. Choices may be restricted by the given
       cart. Return None if not used.

        [
            ('courier', 'Courier'),
            ('standard', 'Standard'),
        ]
    """

    return []


def get_context(cart):
    """Return shipping related context for use in cart related html.
    """
    return {}
