from datetime import datetime
import uuid
import json

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from cart.models import BaseOrderLine, BaseOrder, get_shipping_module
# from dps.models import FullTransactionProtocol, Transaction
# from paypal.models import FullTransactionProtocol, Transaction

from countries import COUNTRY_CHOICES
from .emails import send_email_receipt, send_dispatch_email
import chimp


DEFAULT_CURRENCY = getattr(settings, 'DEFAULT_CURRENCY', 'NZD')


def make_uuid():
    u = uuid.uuid4()
    return str(u).replace('-', '')


class BasePerson(models.Model):
    name = models.CharField(u"Name", max_length=1023, default="")
    street = models.CharField(u"Address", max_length=1023)
    postcode = models.CharField(max_length=100)
    city = models.CharField(u"Town / City", max_length=255)
    state = models.CharField(max_length=255, blank=True, default='')
    country = models.CharField(max_length=2, default=u'New Zealand',
                               choices=COUNTRY_CHOICES)
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

    secret = models.CharField(max_length=32, editable=False, default=make_uuid,
                              unique=True, db_index=True)

    currency = models.CharField(max_length=3, editable=False,
                                default=DEFAULT_CURRENCY)
    created = models.DateTimeField(default=datetime.now)
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=STATUS_NEW)
    tracking_number = models.CharField(blank=True, default='', max_length=50)
    tracking_url = models.URLField(blank=True, default='')
    estimated_delivery = models.DateField(blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2,
                                      default=0)

    account = models.ForeignKey('accounts.Account', null=True, blank=True)
    _shipping_cost = models.DecimalField(
        max_digits=8, decimal_places=2, default=0, db_column='shipping_cost',
        editable=False, verbose_name='shipping cost')
    _shipping_options = models.TextField(
        blank=True, default='', editable=False, db_column='shipping_options',
        verbose_name='shipping options')
    # payments = GenericRelation(Transaction)
    dispatched = models.DateTimeField(null=True, editable=False)
    delivery_notes = models.TextField(blank=True, default='')
    receive_email = models.BooleanField(u"Receive our email news and offers",
                                        default=False)

    def save(self, *args, **kwargs):
        order_qs = Order.objects.filter(pk=self.pk)
        if self.receive_email:
            if not self.pk or order_qs.filter(receive_email=False) \
                                      .update(receive_email=True):
                chimp.subscribe(self.email, self.name.split(' ')[0])
        else:
            if not self.pk or order_qs.filter(receive_email=True) \
                                      .update(receive_email=False):
                chimp.unsubscribe(self.email)

        order = super(Order, self).save(*args, **kwargs)
        if self.status == self.STATUS_SHIPPED and not self.dispatched:
            # Only send the email if the update actually does something,
            # to guard against race conditions
            if Order.objects.filter(pk=self.pk, dispatched__isnull=True) \
                            .update(dispatched=datetime.now()):
                send_dispatch_email(self)
        return order

    def clean(self):
        if self.tracking_number:
            if Order.objects.exclude(pk=self.pk).filter(
                    tracking_number=self.tracking_number):
                raise ValidationError('Tracking numbers must be unique')

    def set_shipping(self, options):
        """Use this method to set shipping options; shipping cost will be
           calculated and saved to the object so it doesn't change if the
           shipping rates change in the future. """

        # actual country overrides whatever is in the options
        recipient = self.get_gift_recipient(create=False)
        options['country'] = recipient.country if recipient else self.country

        self._shipping_options = json.dumps(options)
        shipping_module = get_shipping_module()
        if shipping_module:
            self._shipping_cost = shipping_module.calculate_shipping(self)

    @property
    def shipping_cost(self):
        return self._shipping_cost

    @property
    def shipping_options(self):
        return json.loads(self._shipping_options or '{}')

    @models.permalink
    def get_absolute_url(self):
        return ('checkout_checkout', (self.secret, ))

    @property
    def invoice_number(self):
        return 'TPM-' + str(self.pk).zfill(5)

    def __unicode__(self):
        return u"%s on %s" % (self.name, self.created)

    @property
    def subtotal(self):
        qs = self.lines.filter(return_status__lt=OrderLine.STATUS_RETURNED)
        return sum(line.total for line in qs)

    @property
    def total(self):
        return self.subtotal + self.shipping_cost - self.total_discount

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
        return self.discount_set.all()

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

    def get_lines(self):
        return self.lines.all()

    def get_gift_recipient(self, create=True):
        try:
            return GiftRecipient.objects.get(order=self)
        except GiftRecipient.DoesNotExist:
            return GiftRecipient(order=self) if create else None


class OrderLine(BaseOrderLine):
    STATUS_RETURN_REQUESTED = 1
    STATUS_RETURNED = 2
    STATUS_CHOICES = (
        (0, '---'),
        (STATUS_RETURN_REQUESTED, 'Return requested'),
        (STATUS_RETURNED, 'Item returned'),
    )
    parent_object = models.ForeignKey(Order, related_name='lines')
    return_status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=0)


class GiftRecipient(BasePerson):
    order = models.OneToOneField(Order)
    message = models.TextField(blank=True, default='')

    def __unicode__(self):
        return u"Gift to: %s" % (self.name)


class OrderReturn(models.Model):
    TYPE_CHOICES = (
        ('exchange', 'Exchange'),
        ('return', 'Return'),
    )
    REFUND_TYPE_CHOICES = (
        ('credit', 'Store Credit'),
        ('refund', 'Refund'),
    )
    STATUS_CHOICES = (
        (1, 'In Progress'),
        (2, 'Processed'),
    )

    order = models.OneToOneField(Order)
    created = models.DateTimeField(auto_now_add=True)
    return_type = models.CharField(verbose_name='type', max_length=20,
                                   choices=TYPE_CHOICES,
                                   default=TYPE_CHOICES[0][0])
    exchange_for = models.TextField(default='', blank=True)
    refund_type = models.CharField(max_length=20, choices=REFUND_TYPE_CHOICES,
                                   default=REFUND_TYPE_CHOICES[0][0])
    reason = models.TextField()
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES,
                                              default=1)

    def __unicode__(self):
        return 'Return: %s' % self.order

    class Meta:
        verbose_name = 'return'
