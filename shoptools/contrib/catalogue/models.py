from django.db import models

from shoptools.abstractions.models import ICartItem


class Product(models.Model, ICartItem):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

    # cart integration:

    def cart_line_total(self, line):
        """Returns the total price for quantity of this item as a float. """

        return float(self.price * line.quantity)

    # basic shipping module integration

    def get_shipping_cost(self, line):
        return self.shipping_cost * line.quantity

    def available_options(self):
        return (
            ('Colour', ['Red', 'Blue']),
            ('Message', str),
        )
