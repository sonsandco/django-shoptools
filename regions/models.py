# -*- coding: utf-8 -*-

from django.db import models

from django_countries.fields import CountryField


class RegionQueryset(models.QuerySet):
    pass


class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)
    currency = models.CharField(
        max_length=3, blank=True, default='NZD', help_text=u'3-letter code')
    is_default = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)

    objects = RegionQueryset.as_manager()

    @classmethod
    def get_default(cls):
        return Region.objects.order_by('-is_default').first()

    # def get_default_country(self):
    #     return self.countries.order_by('-is_default_for_region').first()

    def __str__(self):
        return '%s (%s)' % (self.name, self.currency)

    class Meta:
        ordering = ('name', )

    def as_dict(self):
        return {
            'name': self.name,
            'currency': self.currency,
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
            'code': self.country,
        }
