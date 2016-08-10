# -*- coding: utf-8 -*-
import math
from decimal import Decimal

from django.db import models

from countries import COUNTRY_CHOICES


class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)
    currency = models.CharField(
        max_length=3, blank=True, default='NZD', help_text=u'3-letter code',
        editable=False)
    is_default = models.BooleanField(default=False)

    @classmethod
    def get_default(cls):
        return Region.objects.order_by('-is_default').first()

    def get_default_country(self):
        return self.countries.order_by('-is_default_for_region').first()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name', )


class Country(models.Model):
    region = models.ForeignKey(Region, related_name='countries')
    code = models.CharField(max_length=2, choices=COUNTRY_CHOICES, unique=True)
    name = models.CharField(max_length=100, unique=True, editable=False)
    is_default_for_region = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.name = self.get_code_display()
        return super(Country, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'countries'
        ordering = ('name', )


class OptionName(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name', )


class ShippingOption(models.Model):
    region = models.ForeignKey(Region, related_name='options')
    title = models.ForeignKey(OptionName, related_name='shipping_options')

    cost = models.DecimalField(max_digits=8, decimal_places=2)

    def get_shipping_cost(self):
        return self.cost

    def __str__(self):
        return '%s %s' % (self.region.name, self.title.name)

    class Meta:
        ordering = ('region__name', 'cost', 'title__name')
        unique_together = ('region', 'title')
