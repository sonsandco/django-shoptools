# -*- coding: utf-8 -*-

from django.contrib import admin

from utilities.admin_shortcuts import inline_factory, single_page_admin

from .models import OptionName, Region, ShippingOption, Country


admin.site.register(OptionName, **single_page_admin(OptionName))
admin.site.register(Country, **single_page_admin(Country))


class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_default')
    list_editable = ('is_default', )
    inlines = [
        inline_factory(ShippingOption), inline_factory(Country),
    ]
    # form = RegionAdminForm

admin.site.register(Region, RegionAdmin)
