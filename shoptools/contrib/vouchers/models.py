# from datetime import datetime
import uuid
import decimal
from functools import reduce

from django.db import models
from django.db.models import Q
from django.template.defaultfilters import floatformat
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from model_utils.managers import InheritanceManager

from shoptools.cart.base import ICart
from shoptools.checkout.models import Order


def get_vouchers(codes):
    qs = BaseVoucher.objects.select_subclasses()
    if not len(codes):
        return qs.none()
    return qs.filter(reduce(Q.__or__, [Q(code__iexact=c) for c in codes]))


def calculate_discounts(obj, codes, include_shipping=True):
    """Calculate the total discount for an ICart instance, for the given
       voucher codes. Collect a list of Discount instances (unsaved)
       - Multiple percentage vouchers, just take the biggest
       - Multiple fixed vouchers are combined
       - Percentage discounts are applied first, then fixed.

       return (discounts, invalid_codes)
    """

    # TODO is the include_shipping argument really needed?

    assert isinstance(obj, ICart)

    codes = set([c.upper() for c in codes])  # normalise and remove duplicates
    vouchers = get_vouchers(codes)

    discounts = []
    total = obj.subtotal + (decimal.Decimal(obj.shipping_cost)
                            if include_shipping else decimal.Decimal(0))
    # if obj is an order, and the voucher has already been used on that order,
    # those instances are ignored when checking limits etc, since they will be
    # overridden when it's saved. The order is also attached to each Discount
    # instance
    if isinstance(obj, Order):
        defaults = {'order': obj}
    else:
        defaults = {}

    # filter out any that have already been used
    vouchers = [v for v in vouchers if v.available(exclude=defaults)]

    # filter out any under their minimum_spend value
    # invalid_spend = [v for v in vouchers if obj.subtotal < v.minimum_spend]
    vouchers = [v for v in vouchers if obj.subtotal >= v.minimum_spend]

    if include_shipping:
        # apply free shipping (only one)
        shipping = [v for v in vouchers if isinstance(v, FreeShippingVoucher)]
        if len(shipping):
            amount = decimal.Decimal(obj.shipping_cost)
            total -= amount
            discounts.append(
                Discount(voucher=shipping[0], amount=amount, **defaults))

    # TODO make this generic - let apps define their own product-specific
    # vouchers and process them here

    # apply product vouchers (max one per product), using the largest if more
    # than one
    # product = filter(lambda v: isinstance(v, ProductVoucher), vouchers)
    # product.sort(key=lambda v: v.amount_remaining(), reverse=True)
    # products_discounted = []
    # for voucher in product:
    #     # one per product
    #     if voucher.product.id in products_discounted:
    #         continue
    #     products_discounted.append(voucher.product.id)
    #
    #     # get the order total for this specific product
    #     product_total = decimal.Decimal(sum([
    #         line.total for line in obj.get_lines()
    #         if line.item == voucher.product]))
    #
    #     amount = min(product_total, voucher.amount,
    #                  voucher.amount_remaining())
    #     if amount == 0:
    #         continue
    #     total -= amount
    #     discounts.append(Discount(voucher=voucher, amount=amount,
    #                      **defaults))

    # apply fixed vouchers, smallest remaining amount first
    fixed = [v for v in vouchers if isinstance(v, FixedVoucher)]
    fixed.sort(key=lambda v: v.amount_remaining())

    for voucher in fixed:
        amount = min(total, voucher.amount, voucher.amount_remaining())
        if amount == 0:
            continue
        total -= amount
        discounts.append(Discount(voucher=voucher, amount=amount, **defaults))

    # find and apply best percentage voucher
    percentage = [v for v in vouchers if isinstance(v, PercentageVoucher)]
    p_voucher = None
    for voucher in percentage:
        if not p_voucher or p_voucher.amount < voucher.amount:
            p_voucher = voucher

    if p_voucher:
        # percentage discounts can't be used for some products, i.e. gift cards
        p_total = decimal.Decimal(sum([
            line.total for line in obj.get_lines()
            if getattr(line.item, 'allow_discounts', True)]))

        # apply percentage to the smaller of p_total and the running total,
        # because total may have already been discounted, and percentage
        # discount should apply after fixed discounts
        amount = min(total, p_total) * p_voucher.amount / 100

        total -= amount
        discounts.append(
            Discount(voucher=p_voucher, amount=amount, **defaults))

    # identify bad codes and add to the list
    valid_codes = [d.voucher.code.upper() for d in discounts]
    invalid_codes = [c for c in codes if c not in valid_codes]
    return discounts, invalid_codes


def save_discounts(obj, codes):
    assert isinstance(obj, Order)

    discounts, invalid = calculate_discounts(obj, codes)
    for discount in discounts:
        discount.save()


def make_code():
    u = uuid.uuid4()
    return str(u).replace('-', '')[:8]


class BaseVoucher(models.Model):
    code = models.CharField(max_length=32, blank=True, unique=True,
                            help_text="Leave blank to auto-generate")
    created = models.DateTimeField(auto_now_add=True)
    limit = models.PositiveSmallIntegerField(null=True, blank=True)
    minimum_spend = models.PositiveIntegerField(default=0)

    objects = InheritanceManager()

    @property
    def voucher(self):
        qs = BaseVoucher.objects.select_subclasses()
        return qs.get(pk=self.pk)

    @property
    def base_voucher(self):
        return BaseVoucher.objects.get(pk=self.pk)

    def uses(self, exclude={}):
        return Discount.objects.exclude(**exclude) \
                               .filter(base_voucher=self.base_voucher)

    def available(self, exclude={}):
        # FixedVoucher always unlimited uses
        if self.limit is None or isinstance(self.voucher, FixedVoucher):
            return True
        return bool(self.limit - self.uses(exclude).count())

    def amount_redeemed(self, exclude={}):
        uses = self.uses(exclude)
        return uses.aggregate(models.Sum('amount'))['amount__sum'] or 0

    def amount_remaining(self, exclude={}):
        """Return dollar amount remaining on a voucher, where it makes sense.
           If not, return None to indicate an unlimited amount remaining.
        """

        if not isinstance(self.voucher, FixedVoucher):
            return None

        return self.amount - self.amount_redeemed(exclude)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = make_code()
        return super(BaseVoucher, self).save(*args, **kwargs)

    def __str__(self):
        return '%s (%s)' % (self.code, self.voucher.discount_text)


class FixedVoucher(BaseVoucher):
    # need to declare explicitly so it doesn't inherit BaseVoucher's manager
    objects = models.Manager()

    amount = models.DecimalField(max_digits=6, decimal_places=2)
    order_line = models.ForeignKey('checkout.OrderLine', null=True,
                                   editable=False, on_delete=models.SET_NULL)

    @property
    def discount_text(self):
        return '$%s voucher' % floatformat(self.amount, -2)


class PercentageVoucher(BaseVoucher):
    # need to declare explicitly so it doesn't inherit BaseVoucher's manager
    objects = models.Manager()

    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)])

    @property
    def discount_text(self):
        return '%s%% discount' % floatformat(self.amount, -2)


class FreeShippingVoucher(BaseVoucher):
    # need to declare explicitly so it doesn't inherit BaseVoucher's manager
    objects = models.Manager()

    @property
    def discount_text(self):
        return 'free shipping'


class Discount(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    base_voucher = models.ForeignKey(BaseVoucher, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=6, decimal_places=2)

    def __init__(self, *args, **kwargs):
        voucher = kwargs.pop('voucher', None)
        if voucher:
            kwargs['base_voucher'] = voucher.base_voucher
        super(Discount, self).__init__(*args, **kwargs)

    @property
    def voucher(self):
        return self.base_voucher.voucher

    @voucher.setter
    def voucher(self, voucher_obj):
        self.base_voucher = voucher_obj.base_voucher

    def clean(self):
        """Verify that the voucher doesn't violate
           - the usage limit (if there is one)
           - the fixed amount (for fixed vouchers)
           - the total remaining amount (for limited-use, fixed vouchers)
        """

        voucher = self.voucher
        uses = voucher.uses(exclude={'pk': self.pk})

        if voucher.limit is not None and uses.count() > voucher.limit:
            raise ValidationError("Voucher has already been used")

        if isinstance(voucher, FixedVoucher):
            if self.amount > voucher.amount:
                raise ValidationError("Discount exceeds voucher amount")

        remaining = voucher.amount_remaining(exclude={'pk': self.pk})
        if remaining is not None and self.amount > remaining:
            msg = "Discount exceeds voucher's remaining balance"
            raise ValidationError(msg)

    def __str__(self):
        if self.pk:
            return "%s: %s" % (self.order, self.voucher)
        else:
            return str(self.voucher)
