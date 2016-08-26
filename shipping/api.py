def validate_options(options, obj):
    return (options, [], [])


def calculate_shipping_cost(region, option, obj):
    return option.get_shipping_cost()


def save_to_cart(cart, **kwargs):
    from shipping.shipping import Shipping
    return Shipping(**kwargs).save_to(cart)
