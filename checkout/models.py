from datetime import datetime
import uuid
import json

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from cart.models import BaseOrderLine, BaseOrder
# from dps.models import FullTransactionProtocol, Transaction
# from paypal.models import FullTransactionProtocol, Transaction

from countries import COUNTRY_CHOICES
from .emails import send_email_receipt


DEFAULT_CURRENCY = getattr(settings, 'DEFAULT_CURRENCY', 'NZD')


def make_uuid():
    u = uuid.uuid4()
    return str(u).replace('-', '')


# class Order(models.Model, FullTransactionProtocol):
class Order(BaseOrder):

    # values are integers so we can do numeric comparison, i.e.
    # > Order.objects.filter(status__gte=STATUS_PAID) etc
    STATUS_NEW = 1
    STATUS_PAYMENT_FAILED = 2
    STATUS_PAID = 3
    STATUS_SHIPPED = 4

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_PAID, "Paid"),
        (STATUS_PAYMENT_FAILED, "Payment Failed"),
        (STATUS_SHIPPED, "Shipped"),
    ]

    secret = models.CharField(max_length=32, editable=False, default=make_uuid,
                              unique=True, db_index=True)
    name = models.CharField(u"Name", max_length=1023, default="")
    street = models.CharField(u"Address", max_length=1023)
    suburb = models.CharField(max_length=255, blank=True)
    postcode = models.CharField(max_length=100)
    city = models.CharField(u"Town / City", max_length=255)
    country = models.CharField(max_length=2, default=u'New Zealand',
                               choices=COUNTRY_CHOICES)
    email = models.EmailField()
    currency = models.CharField(max_length=3, editable=False,
                                default=DEFAULT_CURRENCY)
    created = models.DateTimeField(default=datetime.now)
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=STATUS_NEW)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2,
                                      default=0)

    account = models.ForeignKey('accounts.Account', null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2,
                                        default=0)
    _shipping_options = models.TextField(blank=True, default='',
                                         db_column='shipping_options')
    # payments = GenericRelation(Transaction)

    def clean(self):
        if self.tracking_number:
            if Order.objects.exclude(pk=self.pk).filter(
                    tracking_number=self.tracking_number):
                raise ValidationError('Tracking numbers must be unique')

    def get_shipping_options(self):
        return json.loads(self._shipping_options or '{}')

    def set_shipping_options(self, opts):
        self._shipping_options = json.dumps(opts)

    shipping_options = property(get_shipping_options, set_shipping_options)

    @models.permalink
    def get_absolute_url(self):
        return ('checkout_checkout', (self.secret, ))

    @property
    def invoice_number(self):
        return str(self.pk).zfill(5)

    def __unicode__(self):
        return u"%s on %s" % (self.name, self.created)

    @property
    def subtotal(self):
        return sum(line.total for line in self.lines.all())

    @property
    def total(self):
        return self.subtotal + self.shipping_cost - self.total_discount

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
                    item.purchase(line.quantity)

        return self.get_absolute_url()

    def transaction_failed(self, transaction=None, interactive=False,
                           status_updated=True):
        if status_updated:
            self.status = self.STATUS_PAYMENT_FAILED
            self.save()

        return self.get_absolute_url()

    def get_lines(self):
        return self.lines.all()


class OrderLine(BaseOrderLine):
    parent_object = models.ForeignKey(Order, related_name='lines')
