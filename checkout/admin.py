from datetime import date
from django.contrib import admin
from django.http import HttpResponse
from django import forms
from django.utils.text import mark_safe

from cart.cart import get_voucher_module

from .models import Order, OrderLine, ShippingAddress, BillingAddress
from .export import generate_csv
from .emails import send_dispatch_email

voucher_mod = get_voucher_module()
voucher_inlines = voucher_mod.get_checkout_inlines() if voucher_mod else []


class ShippingAddressInline(admin.StackedInline):
    model = ShippingAddress
    extra = 0


class BillingAddressInline(admin.StackedInline):
    model = BillingAddress
    extra = 0


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    exclude = ('item_content_type', 'item_object_id', 'created')
    readonly_fields = ('quantity', '_description', '_total', )
    extra = 0

    def has_add_permission(self, request):
        return False


class AddOrderLineForm(forms.ModelForm):
    item = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'variant-autocomplete'}))

    class Meta:
        model = OrderLine
        fields = ('item', 'quantity', )

    def __init__(self, *args, **kwargs):
        super(AddOrderLineForm, self).__init__(*args, **kwargs)

        # from shop.models import Variant
        # self.fields['item'].choices = [
        #     (v.id, str(v)) for v in Variant.objects.all()]

    def save(self, commit=True):
        line = super(AddOrderLineForm, self).save(commit=False)

        from shop.models import Variant

        variant = Variant.objects.get(pk=self.cleaned_data['item'])
        line.item = variant
        variant.purchase(line)
        if commit:
            line.save()
        return line


class AddOrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0
    form = AddOrderLineForm
    fields = ('item', 'quantity')

    def get_queryset(self, request):
        return OrderLine.objects.none()


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('billing_name', 'user', 'billing_email', 'status',
                    'amount_paid', 'created', 'links')
    list_filter = ('status', 'created')
    inlines = [
        ShippingAddressInline,
        BillingAddressInline,
        OrderLineInline,
        AddOrderLineInline,
        # TODO grab transactions as an inline from the payment module - see TPM
    ] + voucher_inlines
    save_on_top = True
    search_fields = ('id', 'billing_address__name', 'billing_address__email',
                     'billing_address__phone', 'billing_address__address',
                     'billing_address__city', 'billing_address__state',
                     'billing_address__postcode', 'shipping_address__name',
                     'shipping_address__email', 'shipping_address__phone',
                     'shipping_address__address', 'shipping_address__city',
                     'shipping_address__state', 'shipping_address__postcode',)
    actions = ('csv_export', 'resend_dispatch_email')
    readonly_fields = ('_shipping_cost', 'id', 'amount_paid', 'currency', )

    def billing_name(self, obj):
        return obj.billing_address.name

    def billing_email(self, obj):
        return obj.billing_address.email

    def resend_dispatch_email(self, request, queryset):
        for order in queryset:
            send_dispatch_email(order)

        self.message_user(request, "Emails sent: %s" % queryset.count())

    # def dispatch(self, request, order_pk):
    #     return
    #
    # def get_urls(self):
    #     urls = super(OrderAdmin, self).get_urls()
    #     return urls + [
    #         url(r'^dispatch/(\d+)$', self.dispatch),
    #     ]

    def csv_export(self, request, queryset):
        filename = 'order_export_' + date.today().strftime('%Y%m%d')

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
        return mark_safe(
            '<a href="%s">View order</a>' % obj.get_absolute_url())
