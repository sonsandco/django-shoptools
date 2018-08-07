from datetime import datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from shoptools.abstractions.models import \
    IShippable, AbstractOrder, AbstractOrderLine
from shoptools.util import make_uuid, get_regions_module
from shoptools import settings as shoptools_settings


class SavedCart(AbstractOrder, IShippable):
    """A db-saved cart class, which can be used interchangeably with Cart. """

    created = models.DateTimeField(default=datetime.now)
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    secret = models.UUIDField(editable=False, default=make_uuid, db_index=True)

    _shipping_option = models.PositiveSmallIntegerField(
        blank=True, null=True, editable=False,
        db_column='shipping_option', verbose_name='shipping option')

    # TODO maybe this should be a JSONField() too? Has to be a list though
    _voucher_codes = models.TextField(
        blank=True, default='', editable=False, db_column='voucher_codes',
        verbose_name='voucher codes')
    order_obj_content_type = models.ForeignKey(
        ContentType, null=True, on_delete=models.SET_NULL)
    order_obj_id = models.PositiveIntegerField(null=True)
    order_obj = GenericForeignKey('order_obj_content_type', 'order_obj_id')

    def get_currency(self):
        regions_module = get_regions_module()
        if regions_module:
            selected_region = regions_module.get_region(self.request)
            if selected_region and selected_region.currency:
                return (selected_region.currency.code,
                        selected_region.currency.symbol)
        return (shoptools_settings.DEFAULT_CURRENCY_CODE,
                shoptools_settings.DEFAULT_CURRENCY_SYMBOL)

    def set_request(self, request):
        self.request = request

    def set_shipping_option(self, option_id):
        """Saves the provided option_id to this SavedCart."""

        self._shipping_option = option_id
        self.save()

    def get_shipping_option(self):
        """Get shipping option for this cart, if any. """
        return self._shipping_option

    def get_voucher_codes(self):
        return filter(bool, self._voucher_codes.split(','))

    def set_voucher_codes(self, codes):
        self._voucher_codes = ','.join(codes)
        self.save()
        return True

    def get_absolute_url(self):
        return reverse('cart_get_cart', args=(self.secret, ))

    def __str__(self):
        if self.user:
            return "Cart by %s, %s" % (self.user.get_full_name(),
                                       self.created)
        else:
            return "Cart, %s" % (self.created, )

    @property
    def total(self):
        return self.subtotal + self.shipping_cost - self.total_discount

    # AbstractOrder integration
    def get_line_cls(self):
        return SavedCartLine

    def save_to(self, obj):
        super(SavedCart, self).save_to(obj)

        # link the order to the cart
        self.order_obj = obj
        self.save()


class SavedCartLine(AbstractOrderLine):
    parent_object = models.ForeignKey(SavedCart, on_delete=models.CASCADE)
