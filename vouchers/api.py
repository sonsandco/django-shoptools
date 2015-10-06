from .models import calculate_discounts, save_discounts
from .admin import DiscountInline


def get_checkout_inlines():
    return [DiscountInline]
