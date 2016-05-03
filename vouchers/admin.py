# -*- coding: utf-8 -*-

from datetime import date

from django.contrib import admin
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from utilities.admin_shortcuts import get_readonly_fields, \
    readonly_inline_factory

from .models import PercentageVoucher, FixedVoucher, Discount, \
    FreeShippingVoucher
from .export import generate_csv


class DiscountAdmin(admin.ModelAdmin):
    readonly_fields = get_readonly_fields(Discount)
    list_display = ('order', 'voucher', 'amount')

    def has_add_permission(self, request):
        return False

admin.site.register(Discount, DiscountAdmin)


DiscountInline = readonly_inline_factory(Discount)


class VoucherAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'limit_', 'minimum_spend', 'code',
                    'created', )
    list_filter = ('created', )

    def limit_(self, obj):
        return obj.limit or ''

admin.site.register(PercentageVoucher, VoucherAdmin)
admin.site.register(FreeShippingVoucher, VoucherAdmin)


class FixedVoucherAdmin(VoucherAdmin):
    list_display = VoucherAdmin.list_display + (
        'order', 'amount_redeemed', 'amount_remaining', )
    actions = ('csv_export', )

    def amount_remaining(self, obj):
        val = obj.amount_remaining()
        return val if val is not None else ''

    def order(self, obj):
        if obj.order_line:
            order = obj.order_line.parent_object
            return u'<a href="%s">%s</a>' % (
                reverse('admin:checkout_order_change', args=(order.pk, )),
                order)
        return ''
    order.allow_tags = True

    def csv_export(self, request, queryset):
        filename = 'PM_vouchers_' + date.today().strftime('%Y%m%d')

        # response = HttpResponse()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = \
            "attachment; filename=%s.csv" % filename

        generate_csv(queryset, response)
        return response
admin.site.register(FixedVoucher, FixedVoucherAdmin)
