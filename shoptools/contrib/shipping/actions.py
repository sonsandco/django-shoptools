from shoptools.cart.actions import cart_action
from .util import available_options_qs


@cart_action(params=(
    ('option_id', int, True),
))
def change_option(cart, option_id):
    """Set shipping option for the given cart """
    available_options = available_options_qs(cart)
    if available_options.filter(id=option_id).count():
        cart.set_shipping_option(option_id)
        return (True, None)
    else:
        return (False, ['Selected shipping option is not available for '
                        'your cart.'])
