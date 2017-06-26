Shipping API
============

`SHOPTOOLS_SHIPPING_MODULE` is a python module which must define `get_errors(cart)`
and `calculate(cart)`. `get_errors` should return a list of error strings, or
an empty list if valid. `calculate` should return the total shipping cost for
the cart.

Shipping modules may also define a `options()` function which returns the
available shipping options. Example output:

    {'postage': ['courier', 'standard'], }

To restrict shipping to a subset of countries, define 
`available_countries(cart)`. This function should return an iterable of 
`(code, name)` tuples.

See shipping.py for a minimal example
