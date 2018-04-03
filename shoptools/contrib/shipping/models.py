# -*- coding: utf-8 -*-

from django.db import models

from shoptools.contrib.regions.models import Region


class Option(models.Model):
    name = models.CharField(max_length=255)
    # TODO delete slug
    slug = models.SlugField(max_length=191, unique=True, editable=False)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ('sort_order', 'name', )

    def __str__(self):
        return self.name


class ShippingOption(models.Model):
    option = models.ForeignKey(Option, related_name='shipping_options',
                               on_delete=models.PROTECT)
    region = models.ForeignKey(Region, related_name='shipping_options',
                               on_delete=models.CASCADE)
    cost = models.DecimalField(verbose_name='cost', max_digits=8,
                               decimal_places=2)
    min_cart_value = models.DecimalField(max_digits=8, decimal_places=2,
                                         default=0)
    max_cart_value = models.DecimalField(max_digits=8, decimal_places=2,
                                         blank=True, null=True)

    @classmethod
    def get_default(cls, region):
        return ShippingOption.objects.filter(region=region).first()

    def __str__(self):
        return '%s (%s)' % (self.option.name, self.region)

    class Meta:
        ordering = ('region__name', 'option', )
