# -*- coding: utf-8 -*-

from django.contrib import admin

try:
    from shipping.admin import ShippingOptionInline
except ImportError:
    ShippingOptionInline = None

from .models import Region, Country


class CountryInline(admin.TabularInline):
    model = Country


class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'currency', 'is_default', 'sort_order', )
    list_editable = ('sort_order', )
    inlines = [CountryInline, ]

    def __init__(self, *args, **kwargs):
        super(RegionAdmin, self).__init__(*args, **kwargs)
        if ShippingOptionInline:
            self.inlines = self.inlines + [ShippingOptionInline, ]


# Don't use admin.register decorator so that we can use super() in init without
# breaking Python 2.x (See
# https://docs.djangoproject.com/en/1.11/ref/contrib/admin/#the-register-decorator).
admin.site.register(Region, RegionAdmin)
