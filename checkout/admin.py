from django.contrib import admin

from cart.admin import orderline_inline_factory

from .models import Order, OrderLine


class OrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'email', 'city', 'country',
                    'amount_paid', 'created', 'links')
    list_filter = ('status', 'created')
    inlines = [
        orderline_inline_factory(OrderLine),
        # TransactionInlineAdmin,
    ]
    save_on_top = True

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return Order.objects.all().order_by('-created')

    def links(self, obj):
        return '<a href="%s">View on site</a>' % obj.get_absolute_url()
    links.allow_tags = True

admin.site.register(Order, OrderAdmin)
