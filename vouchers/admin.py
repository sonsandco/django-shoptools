# -*- coding: utf-8 -*-

from django.contrib import admin

from utilities.admin_shortcuts import get_readonly_fields, \
    readonly_inline_factory

from .models import PercentageVoucher, FixedVoucher, Discount, \
    FreeShippingVoucher


class DiscountAdmin(admin.ModelAdmin):
    readonly_fields = get_readonly_fields(Discount)
    list_display = ('order', 'voucher', 'amount')

    def has_add_permission(self, request):
        return False

admin.site.register(Discount, DiscountAdmin)


DiscountInline = readonly_inline_factory(Discount)


class VoucherAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'limit_', 'code', 'created', )
    list_filter = ('created', )

    def limit_(self, obj):
        return obj.limit or ''

admin.site.register(PercentageVoucher, VoucherAdmin)
admin.site.register(FixedVoucher, VoucherAdmin)
admin.site.register(FreeShippingVoucher, VoucherAdmin)
