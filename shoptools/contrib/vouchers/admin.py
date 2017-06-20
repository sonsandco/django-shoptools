# -*- coding: utf-8 -*-

from datetime import date

from django.contrib import admin
from django.urls import reverse
from django.http import HttpResponse
from django.utils.text import mark_safe

from .models import PercentageVoucher, FixedVoucher, Discount, \
    FreeShippingVoucher
from .export import generate_csv


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    readonly_fields = ('order', 'base_voucher', 'amount', )
    list_display = ('order', 'voucher', 'amount')

    def has_add_permission(self, request):
        return False


class DiscountInline(admin.TabularInline):
    model = Discount
    extra = 0
    max_num = 0
    can_delete = False
    readonly_fields = ('base_voucher', 'amount', )


class VoucherAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'limit_', 'minimum_spend', 'code',
                    'created', )
    list_filter = ('created', )

    def limit_(self, obj):
        return obj.limit or ''


admin.site.register(PercentageVoucher, VoucherAdmin)
admin.site.register(FreeShippingVoucher, VoucherAdmin)


@admin.register(FixedVoucher)
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
            return mark_safe('<a href="%s">%s</a>' % (
                reverse('admin:checkout_order_change', args=(order.pk, )),
                order))
        return ''

    def csv_export(self, request, queryset):
        filename = 'Vouchers_' + date.today().strftime('%Y%m%d')

        # response = HttpResponse()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = \
            "attachment; filename=%s.csv" % filename

        generate_csv(queryset, response)
        return response
