# -*- coding: utf-8 -*-

from django.contrib import admin

from shoptools.contrib.regions.admin import RegionAdmin
from shoptools.contrib.regions.models import Region
from .models import Option, ShippingOption


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name', )}


class ShippingOptionInline(admin.TabularInline):
    model = ShippingOption
    extra = 1


# Add ShippingOptionInline to RegionAdmin
admin.site.unregister(Region)


class RegionAdmin(RegionAdmin):
    def __init__(self, *args, **kwargs):
        super(RegionAdmin, self).__init__(*args, **kwargs)
        self.inlines = self.inlines + (ShippingOptionInline, )


# Don't use admin.register decorator so that we can use super() in init without
# breaking Python 2.x (See
# https://docs.djangoproject.com/en/1.11/ref/contrib/admin/#the-register-decorator).
admin.site.register(Region, RegionAdmin)
