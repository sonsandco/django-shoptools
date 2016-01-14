from datetime import datetime

from django.db import models

from .cart import make_uuid, BaseOrder, BaseOrderLine


class SavedCart(BaseOrder):
    """A db-saved cart class, which can be used interchangeably with Cart. """

    created = models.DateTimeField(default=datetime.now)
    user = models.ForeignKey('auth.User', unique=True)
    secret = models.CharField(max_length=32, editable=False, default=make_uuid,
                              unique=True, db_index=True)

    @models.permalink
    def get_absolute_url(self):
        return ('cart_cart', (self.secret, ))

    def __unicode__(self):
        if self.user:
            return u"Cart by %s, %s" % (self.user.get_full_name(),
                                        self.created)
        else:
            return "Cart, %s" % (self.created, )

    # BaseOrder integration
    def get_line_cls(self):
        return SavedCartLine


class SavedCartLine(BaseOrderLine):
    parent_object = models.ForeignKey(SavedCart)
