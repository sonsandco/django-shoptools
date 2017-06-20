def get_checkout_inlines():
    from .admin import DiscountInline
    return [DiscountInline]


def calculate_discounts(*args, **kwargs):
    from .models import calculate_discounts
    return calculate_discounts(*args, **kwargs)


def save_discounts(*args, **kwargs):
    from .models import save_discounts
    return save_discounts(*args, **kwargs)
