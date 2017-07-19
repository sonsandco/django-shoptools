Shipping API
============

`SHOPTOOLS_SHIPPING_MODULE` is a python module which must define
`calculate(cart)`. This function should return the total shipping cost for
the cart.

Shipping modules may also define an `available_options()` function which
returns an iterable of available shipping option tuples. Example output:

    [
        ('standard', 'Standard Post'),
        ('courier', 'Courier'),
    ]

To restrict shipping to a subset of countries, define
`available_countries(cart)`. This function should return an iterable of
`(code, name)` tuples.

See a `shoptools/contrib/basic_shipping.py` for a minimal example
