from datetime import datetime
import json
import decimal

from django.db import models
from django.conf import settings

from cart.cart import BaseOrderLine, BaseOrder, make_uuid
# from dps.models import FullTransactionProtocol, Transaction
# from paypal.models import FullTransactionProtocol, Transaction

from django_countries.fields import CountryField
from .emails import send_email_receipt, send_dispatch_email


DEFAULT_CURRENCY = getattr(settings, 'DEFAULT_CURRENCY', 'NZD')


class BasePerson(models.Model):
    name = models.CharField(max_length=1023, default="")
    address = models.CharField(max_length=1023)
    postcode = models.CharField(max_length=100)
    city = models.CharField("Town / City", max_length=255)
    state = models.CharField(max_length=255, blank=True, default='')
    country = CountryField()
    email = models.EmailField()
    phone = models.CharField(max_length=50, default='')

    class Meta:
        abstract = True


# class Order(models.Model, FullTransactionProtocol):
class Order(BasePerson, BaseOrder):

    # values are integers so we can do numeric comparison, i.e.
    # > Order.objects.filter(status__gte=STATUS_PAID) etc
    STATUS_NEW = 1
    STATUS_PAYMENT_FAILED = 2
    STATUS_PAID = 3
    STATUS_SHIPPED = 4

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_PAID, "Processing"),
        (STATUS_PAYMENT_FAILED, "Payment Failed"),
        (STATUS_SHIPPED, "Shipped"),
    ]

    id = models.AutoField(verbose_name='Order number', primary_key=True)

    secret = models.UUIDField(editable=False, default=make_uuid, db_index=True)

    currency = models.CharField(max_length=3, editable=False,
                                default=DEFAULT_CURRENCY)
    created = models.DateTimeField(default=datetime.now)
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=STATUS_NEW)
    estimated_delivery = models.DateField(blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2,
                                      default=0)

    user = models.ForeignKey('auth.User', null=True, blank=True,
                             on_delete=models.SET_NULL)
    _shipping_cost = models.DecimalField(
        max_digits=8, decimal_places=2, default=0, db_column='shipping_cost',
        editable=False, verbose_name='shipping cost')
    _shipping_options = models.TextField(
        blank=True, default='', editable=False, db_column='shipping_options',
        verbose_name='shipping options')
    # payments = GenericRelation(Transaction)
    dispatched = models.DateTimeField(null=True, editable=False)
    delivery_notes = models.TextField(blank=True, default='')
    receive_email = models.BooleanField("Receive our email news and offers",
                                        default=False)

    tracking_displayed = models.BooleanField(default=False, editable=False)

    def save(self, *args, **kwargs):
        super(Order, self).save(*args, **kwargs)
        if self.status == self.STATUS_SHIPPED and not self.dispatched:
            # Only send the email if the update actually does something,
            # to guard against race conditions
            if Order.objects.filter(pk=self.pk, dispatched__isnull=True) \
                            .update(dispatched=datetime.now()):
                send_dispatch_email(self)

    def set_shipping(self, options, validate=True):
        '''
            Saves the provided options to this SavedCart. Assumes the
            options have already been validated, if necessary.
        '''
        self._shipping_options = json.dumps(options)
        self._shipping_cost = options.get('cost', 0)
        self.save()

    def get_shipping(self):
        return json.loads(self._shipping_options or '{}')

    @property
    def shipping_cost(self):
        return self._shipping_cost

    @property
    def has_valid_shipping(self):
        return self._shipping_cost is not None

    @models.permalink
    def get_absolute_url(self):
        return ('checkout_checkout', (self.secret, ))

    @property
    def invoice_number(self):
        return str(self.pk).zfill(5)

    def __str__(self):
        return "%s on %s" % (self.name, self.created)

    @property
    def total(self):
        if self.has_valid_shipping:
            return self.subtotal + decimal.Decimal(self.shipping_cost) \
                - self.total_discount
        else:
            return self.subtotal - self.total_discount

    def get_line_cls(self):
        return OrderLine

    # django-dps integration:
    def get_amount(self):
        return max(0, self.total - self.amount_paid)

    # voucher integration
    def calculate_discounts(self):
        # Return actual saved discounts, rather than calculating afresh. This
        # means the discounts are set and won't change if the voucher is
        # removed or modified
        if hasattr(self, 'discount_set'):
            return self.discount_set.all()
        return []

    def is_recurring(self):
        return False

    def transaction_succeeded(self, transaction=None, interactive=False,
                              status_updated=True):
        if status_updated:
            self.amount_paid = \
                self.amount_paid + (transaction.amount if transaction else 0)
            self.status = self.STATUS_PAID
            self.save()
            send_email_receipt(self)

            for line in self.get_lines():
                item = line.item
                if hasattr(item, 'purchase'):
                    item.purchase(line)

        return self.get_absolute_url()

    def transaction_failed(self, transaction=None, interactive=False,
                           status_updated=True):
        if status_updated:
            self.status = self.STATUS_PAYMENT_FAILED
            self.save()

        return self.get_absolute_url()

    def get_gift_recipient(self, create=True):
        try:
            return GiftRecipient.objects.get(order=self)
        except GiftRecipient.DoesNotExist:
            return GiftRecipient(order=self) if create else None


class OrderLine(BaseOrderLine):
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
            self.total = self.item.cart_line_total(
                self.quantity, self.parent_object)

            self.description = self.item.cart_description()

        return super(OrderLine, self).save(*args, **kwargs)


class GiftRecipient(BasePerson):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    delivery_notes = models.TextField(blank=True, default='')
    message = models.TextField(blank=True, default='')

    def __str__(self):
        return "Gift to: %s" % (self.name)
