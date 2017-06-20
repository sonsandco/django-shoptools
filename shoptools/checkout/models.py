from datetime import datetime
import json
import decimal

from django.db import models
from django.conf import settings
from django.urls import reverse

from shoptools.cart.base import AbstractOrderLine, AbstractOrder
from shoptools.cart.util import make_uuid, get_shipping_module
# from dps.models import FullTransactionProtocol, Transaction
# from paypal.models import FullTransactionProtocol, Transaction

from django_countries.fields import CountryField
from .emails import send_email_receipt, send_dispatch_email

# TODO make this configurable
EMAIL_RECEIPT = False
DEFAULT_CURRENCY = getattr(settings, 'DEFAULT_CURRENCY', 'NZD')


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

    currency = models.CharField(max_length=3, editable=False,
                                default=DEFAULT_CURRENCY)
    created = models.DateTimeField(default=datetime.now)
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=STATUS_NEW)
    estimated_delivery = models.DateField(blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2,
                                      default=0)

    delivery_notes = models.TextField(blank=True, default='')
    gift_message = models.TextField(blank=True, default='')

    # TODO review this. It doesn't really belong here
    receive_email = models.BooleanField('Receive our email news and offers',
                                        default=False)

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
    success_page_viewed = models.BooleanField(default=False, editable=False)

    def save(self, *args, **kwargs):
        super(Order, self).save(*args, **kwargs)
        if self.status == self.STATUS_SHIPPED and not self.dispatched:
            # Only send the email if the update actually does something,
            # to guard against race conditions
            if Order.objects.filter(pk=self.pk, dispatched__isnull=True) \
                            .update(dispatched=datetime.now()):
                send_dispatch_email(self)

    def set_shipping_options(self, options, validate=True):
        """Saves the provided options to this order. Assumes the
           options have already been validated, if necessary.
        """

        self._shipping_options = json.dumps(options)
        shipping_module = get_shipping_module()
        if shipping_module:
            self._shipping_cost = shipping_module.calculate(self)
        self.save()

    def get_shipping_options(self):
        return json.loads(self._shipping_options or '{}')

    @property
    def name(self):
        return self.shipping_address.name

    @property
    def email(self):
        return self.shipping_address.email

    @property
    def shipping_cost(self):
        return self._shipping_cost

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
        return "Order #%s" % (self.pk)

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
        return self.get_address(Address.TYPE_BILLING)

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

    def transaction_succeeded(self, amount):
        """Assume this will only be called once per payment. """
        self.amount_paid = models.F('amount_paid') + amount
        # TODO verify that it's fully paid for
        self.status = self.STATUS_PAID
        self.save()

        if EMAIL_RECEIPT:
            send_email_receipt(self)

        for line in self.get_lines():
            item = line.item
            if hasattr(item, 'purchase'):
                item.purchase(line)

    def transaction_failed(self):
        self.status = self.STATUS_PAYMENT_FAILED
        self.save()

    def transaction_success_url(self, transaction):
        return self.get_absolute_url()

    def transaction_failure_url(self, transaction):
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


class AbstractAddress(models.Model):
    """Provides standardized address fields. Also used for account addresses.
    """

    address = models.CharField(max_length=1023)
    city = models.CharField('Town / City', max_length=255)
    postcode = models.CharField(max_length=100)
    state = models.CharField(max_length=255, blank=True, default='')
    country = CountryField()
    phone = models.CharField(max_length=50, default='', blank=True)

    def from_obj(self, obj):
        """Prefill an instance from another AbstractAddress instance. Should
           only be used with subclasses. """

        assert isinstance(obj, AbstractAddress)
        assert issubclass(self.__class__, AbstractAddress)

        fields = ('address',  'city', 'postcode', 'state', 'country',
                  'phone', )
        for f in fields:
            setattr(self, f, getattr(obj, f))

    def as_dict(self):
        return {
            'address': self.address,
            'city': self.city,
            'postcode': self.postcode,
            'state': self.state,
            'country': self.country,
            'phone': self.phone
        }

    class Meta:
        abstract = True


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
    name = models.CharField(max_length=1023, default='')
    email = models.EmailField(blank=True, default='')

    class Meta:
        verbose_name_plural = 'addresses'
        unique_together = ('order', 'address_type')

    def __str__(self):
        return '%s address for %s' % (
            self.get_address_type_display(), self.order)
