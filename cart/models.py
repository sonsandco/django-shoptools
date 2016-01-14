from datetime import datetime
import json

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from .cart import make_uuid, BaseOrder, BaseOrderLine, get_shipping_module, \
    DEFAULT_CURRENCY


class SavedCart(BaseOrder):
    """A db-saved cart class, which can be used interchangeably with Cart. """

    created = models.DateTimeField(default=datetime.now)
    user = models.OneToOneField('auth.User')
    secret = models.CharField(max_length=32, editable=False, default=make_uuid,
                              unique=True, db_index=True)
    _shipping_options = models.TextField(
        blank=True, default='', editable=False, db_column='shipping_options',
        verbose_name='shipping options')
    _voucher_codes = models.TextField(
        blank=True, default='', editable=False, db_column='voucher_codes',
        verbose_name='voucher codes')
    order_obj_content_type = models.ForeignKey(ContentType, null=True)
    order_obj_id = models.PositiveIntegerField(null=True)
    order_obj = GenericForeignKey('order_obj_content_type', 'order_obj_id')
    currency = models.CharField(max_length=3, editable=False,
                                default=DEFAULT_CURRENCY)

    def set_shipping(self, options):
        """Use this method to set shipping options. """

        self._shipping_options = json.dumps(options)
        self.save()

    @property
    def shipping_options(self):
        return json.loads(self._shipping_options or '{}')

    @property
    def shipping_cost(self):
        shipping_module = get_shipping_module()
        if shipping_module:
            return shipping_module.calculate_shipping(self)

    def get_voucher_codes(self):
        return filter(bool, self._voucher_codes.split(','))

    def update_vouchers(self, codes):
        self._voucher_codes = ','.join(codes)
        self.save()
        return True

    @models.permalink
    def get_absolute_url(self):
        return ('cart_cart', (self.secret, ))

    def __unicode__(self):
        if self.user:
            return u"Cart by %s, %s" % (self.user.get_full_name(),
                                        self.created)
        else:
            return "Cart, %s" % (self.created, )

    @property
    def total(self):
        return self.subtotal + self.shipping_cost - self.total_discount

    # BaseOrder integration
    def get_line_cls(self):
        return SavedCartLine

    def save_to(self, obj):
        super(SavedCart, self).save_to(obj)

        # link the order to the cart
        self.order_obj = obj
        self.save()


class SavedCartLine(BaseOrderLine):
    parent_object = models.ForeignKey(SavedCart)
