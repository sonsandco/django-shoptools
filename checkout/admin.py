from django.contrib import admin

from cart.admin import orderline_inline_factory
from cart.models import get_voucher_module

from .models import Order, OrderLine, GiftRecipient


voucher_mod = get_voucher_module()
voucher_inlines = voucher_mod.get_checkout_inlines() if voucher_mod else []


class GiftRecipientInline(admin.StackedInline):
    model = GiftRecipient
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'email', 'city', 'country',
                    'amount_paid', 'created', 'tracking_number', 'links')
    list_filter = ('status', 'created')
    inlines = [
        GiftRecipientInline,
        orderline_inline_factory(OrderLine),
    ] + voucher_inlines
    save_on_top = True

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return Order.objects.all().order_by('-created')

    def links(self, obj):
        return '<a href="%s">View on site</a>' % obj.get_absolute_url()
    links.allow_tags = True

admin.site.register(Order, OrderAdmin)
