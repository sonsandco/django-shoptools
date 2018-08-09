# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import Currency, Region, Country
from shoptools.util import get_shipping_module


shipping_module = get_shipping_module()
shipping_inlines = getattr(shipping_module, 'get_region_inlines',
                           lambda *args: [])() if shipping_module else []


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'symbol')


class CountryInline(admin.TabularInline):
    model = Country


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'currency', 'is_default', 'sort_order', )
    list_editable = ('sort_order', )
    inlines = [CountryInline, ] + shipping_inlines
