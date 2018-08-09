# -*- coding: utf-8 -*-
"""
Basic example shipping module which calculates total shipping based on the
shipping_cost for each item in the cart.
"""


def calculate(cart):
    """Return the total shipping cost for the cart. """

    total = 0
    for line in cart.get_lines():
        total += line.item.shipping_cost * line.quantity
    return total


def get_context(cart):
    return {}
