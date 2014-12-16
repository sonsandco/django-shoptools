from django.contrib import admin
from django.contrib.contenttypes import generic

from cart.admin import OrderLineInlineAdmin
from paypal.admin import TransactionInlineAdmin

from models import Order


class OrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'city', 'country', 'amount_paid', 'created', 'links')
    list_filter = ('status', 'created')
    inlines = [OrderLineInlineAdmin, TransactionInlineAdmin]
    save_on_top = True
    
    def get_queryset(self, request):
        return Order.objects.all().order_by('-created')
    
    def links(self, obj):
        return '<a href="%s">View on site</a>' % obj.get_absolute_url()
    links.allow_tags = True

admin.site.register(Order, OrderAdmin)
