
def calculate_shipping(items, options=None, order=None):
    '''Return shipping cost for the given order lines, which could be from
       a session cart or a db-saved order. Either an options dict, or an
       Order instance will be passed, but not both.'''

    assert (options is None) != (order is None), \
        'Pass options or order, not both'

    return 0
