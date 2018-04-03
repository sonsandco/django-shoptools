# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import Region, Country


class CountryInline(admin.TabularInline):
    model = Country


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'currency', 'is_default', 'sort_order', )
    list_editable = ('sort_order', )
    exclude = ('symbol', )  # symbol not implemented yet
    inlines = (CountryInline, )
