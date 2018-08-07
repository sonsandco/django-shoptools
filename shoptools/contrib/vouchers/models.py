# from datetime import datetime
import uuid

from django.db import models
from django.template.defaultfilters import floatformat
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from model_utils.managers import InheritanceManager

from shoptools import settings as shoptools_settings
from shoptools.checkout.models import Order, OrderLine


def make_code():
    u = uuid.uuid4()
    return str(u).replace('-', '')[:8]


class BaseVoucher(models.Model):
    code = models.CharField(max_length=32, blank=True, unique=True,
                            help_text="Leave blank to auto-generate")
    created = models.DateTimeField(auto_now_add=True)
    limit = models.PositiveSmallIntegerField(null=True, blank=True)
    minimum_spend = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField(blank=True, null=True)

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
    # Save code itself instead of a foreignKey to Currency, as regions app may
    # not be enabled. This also avoids issues if the client deletes the
    # Currency.
    currency_code = models.CharField(
        max_length=4, editable=False,
        default=shoptools_settings.DEFAULT_CURRENCY_CODE)
    currency_symbol = models.CharField(
        max_length=1, editable=False,
        default=shoptools_settings.DEFAULT_CURRENCY_SYMBOL)
    order_line = models.ForeignKey(OrderLine, null=True, editable=False,
                                   on_delete=models.SET_NULL)

    @property
    def discount_text(self):
        return '%s%s voucher' % (self.currency_symbol,
                                 floatformat(self.amount, -2))


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
