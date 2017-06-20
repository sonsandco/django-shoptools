# -*- coding: utf-8 -*-
"""
Basic example shipping module which delegates the shipping calculation to the
product's get_shipping_cost method, and restricts shipping destination to
countries within the current region.
"""


from shoptools.regions.util import get_region


def get_errors(cart):
    """Return a list of error strings, or an empty list if valid. """

    return []


def calculate(cart):
    """Return the total shipping cost for the cart. """

    total = 0
    for line in cart.get_lines():
        total += line.item.get_shipping_cost(line)

    return total


def available_countries(cart):
    """Return iterable of country choices which this cart could be shipped to.
       Choices should be of the form (country_code, country_name)
       Return None if there's no restriction. """

    region = get_region(cart.request)
    return ((c.country.code, c.country.name) for c in region.countries.all())


def options(cart):
    """Return the shipping options as a list of two-tuples, suitable for use by
       a django forms ChoiceField. Choices may be restricted by the given
       cart. Return None if not used.

        [
            ('courier', 'Courier'),
            ('standard', 'Standard'),
        ]
    """

    return None
