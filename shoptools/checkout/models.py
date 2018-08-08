from datetime import datetime
import decimal

from django.db import models
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from shoptools import settings as shoptools_settings
from shoptools.abstractions.models import \
    AbstractOrderLine, AbstractOrder, AbstractAddress
from shoptools.util import make_uuid, get_shipping_module

from .emails import send_email_receipt, send_dispatch_email
from .signals import \
    checkout_post_payment_pre_success, checkout_post_payment_post_success, \
    checkout_post_payment_pre_failure, checkout_post_payment_post_failure

# TODO make this configurable
EMAIL_RECEIPT = True


class Order(AbstractOrder):

    # values are integers so we can do numeric comparison, i.e.
    # > Order.objects.filter(status__gte=STATUS_PAID) etc
    STATUS_NEW = 1
    STATUS_PAYMENT_FAILED = 2
    STATUS_PAID = 3
    STATUS_SHIPPED = 4

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_PAYMENT_FAILED, "Payment Failed"),
        (STATUS_PAID, "Paid"),
        (STATUS_SHIPPED, "Shipped"),
    ]

    id = models.AutoField(verbose_name='Order number', primary_key=True)

    secret = models.UUIDField(editable=False, default=make_uuid, db_index=True)

    # hardcode currency in case the client subsequently deletes it in the admin
    currency_code = models.CharField(
        max_length=4, editable=False,
        default=shoptools_settings.DEFAULT_CURRENCY_CODE)
    currency_symbol = models.CharField(
        max_length=1, editable=False,
        default=shoptools_settings.DEFAULT_CURRENCY_SYMBOL)
    created = models.DateTimeField(default=datetime.now)
    checkout_completed = models.DateTimeField(blank=True, null=True)
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=STATUS_NEW)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2,
                                      default=0)

    delivery_notes = models.TextField(blank=True, default='')
    gift_message = models.TextField(blank=True, default='')


    user = models.ForeignKey('auth.User', null=True, blank=True,
                             on_delete=models.SET_NULL)
    _shipping_cost = models.DecimalField(
        max_digits=8, decimal_places=2, default=0, db_column='shipping_cost',
        editable=False, verbose_name='shipping cost')
    _shipping_option = models.PositiveSmallIntegerField(
        blank=True, null=True, editable=False,
        db_column='shipping_option', verbose_name='shipping option')

    dispatched = models.DateTimeField(null=True, editable=False)
    success_page_viewed = models.BooleanField(default=False, editable=False)

    def save(self, *args, **kwargs):
        super(Order, self).save(*args, **kwargs)
        if self.status == self.STATUS_SHIPPED and not self.dispatched:
            # Only send the email if the update actually does something,
            # to guard against race conditions
            if Order.objects.filter(pk=self.pk, dispatched__isnull=True) \
                            .update(dispatched=datetime.now()):
                send_dispatch_email(self)

    def set_request(self, request):
        self.request = request

    def set_shipping_option(self, option_id):
        """Saves the provided option_id to this order."""
        self._shipping_option = option_id
        shipping_module = get_shipping_module()
        if shipping_module:
            self._shipping_cost = shipping_module.calculate(self)
        self.save()

    def get_shipping_option(self):
        return self._shipping_option

    def get_currency(self):
        return (self.currency_code, self.currency_symbol)

    @property
    def shipping_cost(self):
        return self._shipping_cost

    @property
    def name(self):
        return self.shipping_address.name

    @property
    def email(self):
        return self.shipping_address.email

    # @property
    # def has_valid_shipping(self):
    #     return self._shipping_cost is not None

    def get_absolute_url(self):
        return reverse('checkout_checkout', args=(self.secret, ))

    @property
    def description(self):
        return '%s items' % self.count()

    @property
    def invoice_number(self):
        return str(self.pk).zfill(5)

    def __str__(self):
        return 'Order #%s' % (self.pk)

    @property
    def total(self):
        return self.subtotal + decimal.Decimal(self.shipping_cost) \
            - self.total_discount

    def get_line_cls(self):
        return OrderLine

    def get_address(self, address_type, create=False):
        params = {
            'address_type': address_type,
            'order': self,
        }
        try:
            return Address.objects.get(**params)
        except Address.DoesNotExist:
            if create:
                return Address(**params)
        return None

    @property
    def shipping_address(self):
        return self.get_address(Address.TYPE_SHIPPING, True)

    @property
    def billing_address(self):
        billing = self.get_address(Address.TYPE_BILLING)
        if not billing:
            billing = self.get_address(Address.TYPE_SHIPPING)
        return billing

    # voucher integration
    def calculate_discounts(self):
        # Return actual saved discounts, rather than calculating afresh. This
        # means the discounts are set and won't change if the voucher is
        # removed or modified
        if hasattr(self, 'discount_set'):
            return self.discount_set.all(), None
        return ([], None)

    # payment integration:
    def is_recurring(self):
        return False

    def get_amount(self):
        return max(0, self.total - self.amount_paid)

    def transaction_succeeded(self, transaction=None, interactive=None,
                              status_updated=None):
        """Assumes this will only be called once per payment. """
        checkout_post_payment_pre_success.send(
            sender=Order, transaction=transaction, interactive=interactive,
            status_updated=status_updated)

        needs_save = False

        if transaction:
            complete = self.get_amount() <= transaction.amount
            self.amount_paid = models.F('amount_paid') + transaction.amount
            needs_save = bool(transaction.amount)
        else:
            complete = self.get_amount()

        if complete:
            self.status = self.STATUS_PAID
            self.checkout_completed = datetime.now()
            needs_save = True

        if needs_save:
            self.save()

        if complete:
            if EMAIL_RECEIPT:
                send_email_receipt(self)

            for line in self.get_lines():
                item = line.item
                if hasattr(item, 'purchase'):
                    item.purchase(line)

        checkout_post_payment_post_success.send(
            sender=Order, transaction=transaction, interactive=interactive,
            status_updated=status_updated)

    def transaction_failed(self, transaction=None, interactive=None,
                           status_updated=None):
        checkout_post_payment_pre_failure.send(
            sender=Order, transaction=transaction, interactive=interactive,
            status_updated=status_updated)

        self.status = self.STATUS_PAYMENT_FAILED
        self.save()

        checkout_post_payment_post_failure.send(
            sender=Order, transaction=transaction, interactive=interactive,
            status_updated=status_updated)

    def transaction_success_url(self):
        return self.get_absolute_url()

    def transaction_failure_url(self):
        return self.get_absolute_url()


class OrderLine(AbstractOrderLine):
    parent_object = models.ForeignKey(Order, related_name='lines',
                                      on_delete=models.CASCADE)
    _total = models.DecimalField(max_digits=8, decimal_places=2,
                                 db_column='total')
    _description = models.CharField(max_length=255, blank=True,
                                    db_column='description')

    def set_total(self, val):
        self._total = val
    total = property(lambda s: s._total, set_total)

    def set_description(self, val):
        self._description = val
    description = property(lambda s: s._description, set_description)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.total = self.item.cart_line_total(self)

            self.description = self.item.cart_description()

        return super(OrderLine, self).save(*args, **kwargs)


class Address(AbstractAddress):
    TYPE_SHIPPING = 'shipping'
    TYPE_BILLING = 'billing'
    TYPE_CHOICES = (
        (TYPE_SHIPPING, 'Shipping'),
        (TYPE_BILLING, 'Billing'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              related_name='addresses')
    address_type = models.CharField(choices=TYPE_CHOICES,
                                    default=TYPE_SHIPPING, max_length=20)
    first_name = models.CharField(max_length=1023, default='')
    last_name = models.CharField(max_length=1023, default='')
    email = models.EmailField(default='')

    @property
    def name(self):
        return '%s %s' % (self.first_name, self.last_name)

    class Meta:
        verbose_name_plural = 'addresses'
        unique_together = ('order', 'address_type')

    def __str__(self):
        return '%s address for %s' % (
            self.get_address_type_display(), self.order)
