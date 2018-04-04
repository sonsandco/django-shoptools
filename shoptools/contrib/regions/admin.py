# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import Currency, Region, Country


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'symbol')


class CountryInline(admin.TabularInline):
    model = Country


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'currency', 'is_default', 'sort_order', )
    list_editable = ('sort_order', )
    inlines = (CountryInline, )
