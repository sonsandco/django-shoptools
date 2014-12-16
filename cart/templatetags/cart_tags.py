from coffin import template
from cart.models import Cart

register = template.Library()
register.object("Cart", Cart)
