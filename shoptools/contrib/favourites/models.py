from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from shoptools.abstractions.models \
    import AbstractOrder, AbstractOrderLine, ICartItem
from shoptools.util import make_uuid
from shoptools.cart import get_cart


class FavouritesList(AbstractOrder):
    """
    Represents a list of favourites (or wishlist / registry), db persisted in
    the same manner as SavedCart. Items capable of being favourited are
    required to inherit from ICartItem.

    Each user can have multiple FavouritesLists, which therefore must be named.
    """
    created = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE,
                             related_name='favourites_lists')
    secret = models.UUIDField(editable=False, default=make_uuid, db_index=True)
    name = models.CharField(max_length=191)

    @property
    def total(self):
        return self.subtotal

    class Meta:
        ordering = ('-created', )

    def get_absolute_url(self):
        return reverse('favourites_detail', args=(self.secret, ))

    def get_currency(self, request):
        return get_cart(request).get_currency()

    def __str__(self):
        return self.name

    # AbstractOrder integration
    def set_request(self, request):
        self.request = request

    def get_line_cls(self):
        return FavouritesLine

    def as_dict(self):
        data = {
            'count': self.count(),
            'lines': [line.as_dict() for line in self.get_lines()],
        }

        return data


class FavouritesItem(models.Model, ICartItem):
    """
    Every item added to a FavouritesLine will be an instance of FavouritesItem.
    Each FavouritesItem in turn has a GenericForeignKey named item. All of
    FavouritesItem's ICartItem related methods delegate off to the applicable
    method of item, and the purchase method additionally decrements the
    FavouritesLine quantity.

    This structure is so that an instance of FavouritesItem can be added to
    the cart directly and will behave like item was in the cart instead, except
    that the FavouritesLine quantity will also be decremented on purchase to
    support gift registry functionality.

    You are expected to only add a FavouritesItem to the cart if item inherits
    from ICartItem, and the purchaseable property is provided to assist in
    this. Attempting to add a FavouritesItem to the cart where item is not a
    subclass of ICartItem will result in an AssertionError.
    """
    favourites_list = models.ForeignKey(
        FavouritesList, on_delete=models.CASCADE,
        related_name='favourites_items')

    item_content_type = models.ForeignKey(ContentType,
                                          on_delete=models.PROTECT)
    item_object_id = models.PositiveIntegerField()
    item = GenericForeignKey('item_content_type', 'item_object_id')

    @property
    def purchaseable(self):
        if getattr(self, '_purchaseable', None) is None:
            self._purchaseable = issubclass(type(self.item), ICartItem)
        return self._purchaseable

    @property
    def item_ctype(self):
        assert self.purchaseable, 'item must be a subclass of ICartItem'
        return self.item.ctype

    def cart_line_total(self, line):
        assert self.purchaseable, 'item must be a subclass of ICartItem'
        return self.item.cart_line_total(line)

    def purchase(self, line):
        assert self.purchaseable, 'item must be a subclass of ICartItem'
        # attempt item purchase first, so if there is any kind of error the
        # FavouritesLine quantity is not changed.
        rv = self.item.purchase(line)
        # line here is the CartLine, not FavouritesLine
        favourites_line = line.item.favourites_list.get_line(line.item, {})
        favourites_line.quantity = favourites_line.quantity - line.quantity
        favourites_line.save()
        return rv

    def cart_errors(self, line):
        assert self.purchaseable, 'item must be a subclass of ICartItem'
        errors = []
        if not isinstance(line, FavouritesLine):
            favourites_line = line.item.favourites_list.get_line(line.item, {})
            # If this line is missing from favourites, remove it from the cart
            if not favourites_line:
                errors.append(
                    '%s was removed from your cart because it is not longer '
                    'part of %s.' % (line.item, line.item.favourites_list))
                line.parent_object.update_quantity(line.item, 0)
            else:
                # Reduce quantity to match remaining items in favourites list,
                # if necessary
                max = favourites_line.quantity
                if line.quantity > max:
                    errors.append(
                        '%s does not include as many %s as you have ordered. '
                        'The amount in your cart has been reduced to %d.' %
                        (line.item.favourites_list, line.item, max))
                    line.parent_object.update_quantity(line.item, max)
        return errors + self.item.cart_errors(line)

    def cart_description(self):
        assert self.purchaseable, 'item must be a subclass of ICartItem'
        return self.item.cart_description()

    def available_options(self):
        assert self.purchaseable, 'item must be a subclass of ICartItem'
        return self.item.available_options()

    def default_options(self):
        assert self.purchaseable, 'item must be a subclass of ICartItem'
        return self.item.default_options()

    def get_absolute_url(self):
        return getattr(self.item, 'get_absolute_url', lambda: '')()

    def __str__(self):
        return str(self.item)


class FavouritesLine(AbstractOrderLine):
    parent_object = models.ForeignKey(FavouritesList, on_delete=models.CASCADE)
