# -*- coding: utf-8 -*-
"""
Basic example shipping module which delegates the shipping calculation to the
product's get_shipping_cost method, and restricts shipping destination to
countries within the current region.
"""

from django.db.models import Q

from shoptools.contrib.regions.util import get_region
from .models import ShippingOption
from .forms import ShippingOptionSelectionForm


def available_countries(cart):
    """Return iterable of country choices which this cart could be shipped to.
       Choices should be of the form (country_code, country_name)
    """

    region = get_region(cart.request)
    return [(c.country.code, c.country.name) for c in region.countries.all()]


def available_options_qs(cart):
    """Return available Options for this cart """

    region = get_region(cart.request)

    region_query = Q(region=region)
    min_query = Q(min_cart_value__lte=cart.subtotal)
    max_query = \
        Q(max_cart_value__isnull=True) | \
        Q(max_cart_value__gte=cart.subtotal)

    return ShippingOption.objects.filter(
        region_query, min_query, max_query).distinct()


def available_options(cart):
    """Return iterable of shipping option choices applicable to this cart.
       Choices should be of the form
       (shipping_option_id, shipping_option_id)
    """
    return available_options_qs(cart).values_list('id', 'option__name')


def calculate(cart):
    """Return the total shipping cost for the cart. """

    if not hasattr(cart, 'get_shipping_option'):
        raise NotImplementedError()
    option_id = cart.get_shipping_option()
    region = get_region(cart.request)

    region_query = Q(region=region)
    min_query = Q(min_cart_value__lte=cart.subtotal)
    max_query = Q(max_cart_value__isnull=True) | \
        Q(max_cart_value__gte=cart.subtotal)

    options = ShippingOption.objects.filter(
        region_query, min_query, max_query, id=option_id)
    option = options.order_by('cost').first()

    if option:
        return option.cost

    return 0


def shipping_context(cart):
    """Return shipping related context for use in cart related html.
    """
    available_shipping_options = list(available_options(cart))
    selected_option_id = cart.get_shipping_option()
    selected_shipping_option = None
    try:
        selected_shipping_option = \
            ShippingOption.objects.get(id=selected_option_id)
    except ShippingOption.DoesNotExist:
        pass

    initial = {}

    if selected_option_id:
        initial['shipping_option'] = selected_option_id

    if selected_option_id not in \
            [opt_id for (opt_id, name) in available_shipping_options]:
        # prepend a blank one if the current option is invalid
        available_shipping_options = ((None, 'Select shipping option'), ) + \
            tuple(available_shipping_options)
        initial = {}

    shipping_option_selection_form = ShippingOptionSelectionForm(
        initial=initial,
        shipping_option_choices=available_shipping_options)

    return {
        'available_shipping_options': available_shipping_options,
        'selected_shipping_option': selected_shipping_option,
        'shipping_option_selection_form': shipping_option_selection_form
    }
