# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import Option, ShippingOption


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index, while
        still allowing instances to be added, deleted and edited via the + / -
        buttons next to RelatedWidgets.
        """
        return {}


class ShippingOptionAdmin(admin.ModelAdmin):
    list_display = ('option', 'region', 'cost', 'min_cart_value',
                    'max_cart_value')


class ShippingOptionInline(admin.TabularInline):
    model = ShippingOption
    extra = 1
