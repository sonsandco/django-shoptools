from datetime import date
from django.contrib import admin
from django.http import HttpResponse
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django import forms

from cart.models import get_voucher_module

from .models import Order, OrderLine, GiftRecipient
from .export import generate_csv

voucher_mod = get_voucher_module()
voucher_inlines = voucher_mod.get_checkout_inlines() if voucher_mod else []


class GiftRecipientInline(admin.StackedInline):
    model = GiftRecipient
    extra = 0


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    exclude = ('item_content_type', 'item_object_id', 'created')
    readonly_fields = ('quantity', 'description', 'total', )
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
        #     (v.id, unicode(v)) for v in Variant.objects.all()]

    def save(self, commit=True):
        line = super(AddOrderLineForm, self).save(commit=False)

        from shop.models import Variant

        variant = Variant.objects.get(pk=self.cleaned_data['item'])
        line.item = variant
        line.description = variant.cart_description()
        line.total = variant.cart_line_total(line.quantity)
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


class OrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'email', 'status',
                    'amount_paid', 'created', 'links')
    list_filter = ('status', 'created')
    inlines = [
        GiftRecipientInline,
        OrderLineInline,
        AddOrderLineInline,
    ] + voucher_inlines
    save_on_top = True
    readonly_fields = ('_shipping_cost', 'id')
    actions = ('csv_export', 'resend_dispatch_email')

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
