def get_checkout_inlines():
    from .admin import DiscountInline
    return [DiscountInline]


def calculate_discounts(*args, **kwargs):
    from .util import calculate_discounts
    return calculate_discounts(*args, **kwargs)


def save_discounts(*args, **kwargs):
    from .util import save_discounts
    return save_discounts(*args, **kwargs)


def get_context(request):
    from .util import vouchers_context
    return vouchers_context(request)
