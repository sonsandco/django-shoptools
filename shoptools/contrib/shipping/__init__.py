
def calculate(cart):
    from .util import calculate
    return calculate(cart)


def available_countries(cart):
    from .util import available_countries
    return available_countries(cart)


def available_options(cart):
    from .util import available_options
    return available_options(cart)


def get_context(request):
    from .util import shipping_context
    return shipping_context(request)


def get_shipping_option_instance(shipping_option_id):
    from .models import ShippingOption
    return ShippingOption.objects.get(id=shipping_option_id)


def get_region_inlines():
    from .admin import ShippingOptionInline
    return [ShippingOptionInline]
