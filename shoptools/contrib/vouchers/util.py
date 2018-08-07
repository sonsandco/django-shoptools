import decimal
from datetime import date
from functools import reduce

from django.db.models import Q

from shoptools.util import get_vouchers_module
from shoptools.abstractions.models import ICart
from shoptools.checkout.models import Order

from .models import \
    BaseVoucher, FreeShippingVoucher, Discount, FixedVoucher, PercentageVoucher


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
    # if obj is or has an associated an order, and the voucher has already been
    # used on that order, those instances are ignored when checking limits etc,
    # since they will be overridden when it's saved. The order is also attached
    # to each Discount instance
    if isinstance(obj, Order):
        defaults = {'order': obj}
    else:
        o = getattr(obj, 'order_obj', None)
        if o and not o.amount_paid:
            defaults = {'order': o}
        else:
            defaults = {}

    # filter out any that have already been used
    vouchers = [v for v in vouchers if v.available(exclude=defaults)]

    # filter out any that are expired
    vouchers = [v for v in vouchers if
                (not v.expiry_date or v.expiry_date >= date.today())]

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
    fixed.sort(key=lambda v: v.amount_remaining(exclude=defaults))

    for voucher in fixed:
        # exclude any vouchers that do not match the cart's currency
        cart_currency_code, _ = obj.get_currency()
        if voucher.currency_code != cart_currency_code:
            continue

        amount = min(total, voucher.amount,
                     voucher.amount_remaining(exclude=defaults))
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


def vouchers_context(request):
    vouchers_module = get_vouchers_module()
    vouchers_enabled = bool(vouchers_module)

    return {
        'vouchers_enabled': vouchers_enabled
    }
