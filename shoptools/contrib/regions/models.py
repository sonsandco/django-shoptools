# -*- coding: utf-8 -*-

from django.db import models

from django_countries.fields import CountryField

from shoptools import settings as shoptools_settings
from shoptools.currencies import CURRENCIES


# TODO: Own app?
class Currency(models.Model):
    code = models.CharField(
        verbose_name='type',
        max_length=4, unique=True, choices=CURRENCIES,
        default=shoptools_settings.DEFAULT_CURRENCY_CODE)
    symbol = models.CharField(
        max_length=1, default=shoptools_settings.DEFAULT_CURRENCY_SYMBOL)

    class Meta:
        verbose_name_plural = 'currencies'

    def __str__(self):
        return self.get_code_display()


class RegionQueryset(models.QuerySet):
    pass


class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)
    currency = models.ForeignKey(Currency, related_name='regions')
    currency = models.ForeignKey(Currency, related_name='regions',
                                 on_delete=models.CASCADE)
    is_default = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)

    objects = RegionQueryset.as_manager()

    @classmethod
    def get_default(cls):
        return Region.objects.order_by('-is_default').first()

    @property
    def option_text(self):
        if self.currency:
            return '%s (%s)' % (self.name, self.currency.code)
        return self.name

    # def get_default_country(self):
    #     return self.countries.order_by('-is_default_for_region').first()

    def __str__(self):
        if self.currency:
            return '%s (%s)' % (self.name, self.currency.code)
        return self.name

    class Meta:
        ordering = ('name', )

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'currency_code': self.currency.code,
            'currency_symbol': self.currency.symbol,
        }


class Country(models.Model):
    region = models.ForeignKey(Region, related_name='countries',
                               on_delete=models.CASCADE)
    country = CountryField(unique=True)
    # is_default_for_region = models.BooleanField(default=False)

    def __str__(self):
        return self.get_country_display()

    class Meta:
        verbose_name_plural = 'countries'
        ordering = ('country', )

    def as_dict(self):
        return {
            'name': self.get_country_display(),
            'code': self.country.code,
        }
