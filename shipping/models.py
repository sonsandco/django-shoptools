# -*- coding: utf-8 -*-

from django.db import models

from regions.models import Region


class ShippingOption(models.Model):
    name = models.CharField(max_length=255)
    region = models.ForeignKey(Region, related_name='shipping_options',
                               on_delete=models.CASCADE)
    _cost = models.DecimalField(verbose_name='cost', max_digits=8,
                                decimal_places=2, db_column='cost')
    is_default = models.BooleanField(default=False)

    def get_cost(self, cart=None):
        # Optionally implement additional logic here, for example if _cost is
        # per item, rather than in total.
        return self._cost

    @classmethod
    def get_default(cls, region):
        return ShippingOption.objects.filter(region=region) \
                             .order_by('-is_default').first()

    def as_dict(self, cart=None):
        return {
            'id': self.id,
            'region': self.region.id,
            'name': self.name,
            'cost': self.get_cost(cart),
        }

    def __str__(self):
        return '%s %s' % (self.region.name, self.name)

    class Meta:
        ordering = ('region__name', '_cost', 'name')
        unique_together = ('region', 'name')
