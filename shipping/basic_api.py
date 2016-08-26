def calculate_shipping_cost(obj):
    return 0


def save_to_cart(cart, **kwargs):
    cost = calculate_shipping_cost(cart)
    shipping = {
        'cost': float(cost) if (cost or cost == 0) else None
    }
    cart.set_shipping(shipping)
    return shipping
