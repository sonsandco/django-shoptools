from .models import calculate_discounts, save_discounts, get_vouchers
from .admin import DiscountInline


def get_checkout_inlines():
    return [DiscountInline]
