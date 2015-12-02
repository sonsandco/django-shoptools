from datetime import date
from django.contrib import admin
from django.http import HttpResponse
from django.conf.urls import url

from cart.admin import orderline_inline_factory
from cart.models import get_voucher_module

from .models import Order, OrderLine, GiftRecipient
from .export import generate_csv

voucher_mod = get_voucher_module()
voucher_inlines = voucher_mod.get_checkout_inlines() if voucher_mod else []


class GiftRecipientInline(admin.StackedInline):
    model = GiftRecipient
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'email', 'status',
                    'amount_paid', 'created', 'links')
    list_filter = ('status', 'created')
    inlines = [
        GiftRecipientInline,
        orderline_inline_factory(OrderLine),
    ] + voucher_inlines
    save_on_top = True
    actions = ('csv_export', )
    readonly_fields = ('_shipping_cost', 'id')

    def dispatch(self, request, order_pk):
        return

    def get_urls(self):
        urls = super(OrderAdmin, self).get_urls()
        return urls + [
            url(r'^dispatch/(\d+)$', self.dispatch),
        ]

    def csv_export(self, request, queryset):
        filename = 'PM_export_' + date.today().strftime('%Y%m%d')

        # response = HttpResponse()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = \
            "attachment; filename=%s.csv" % filename

        generate_csv(queryset, response)
        return response

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return Order.objects.all().order_by('-created')

    def links(self, obj):
        return '<a href="%s">View order</a>' % obj.get_absolute_url()
    links.allow_tags = True

admin.site.register(Order, OrderAdmin)
