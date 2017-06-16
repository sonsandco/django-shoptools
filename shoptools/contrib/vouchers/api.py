# Do not remove these imports, even though they are unused in this file, they
# are necessary as this serves as the entry point to the application and will
# therefore be imported from this file elsewhere.
from .models import calculate_discounts, save_discounts
from .admin import DiscountInline


def get_checkout_inlines():
    return [DiscountInline]
