from datetime import datetime

from django.db import models
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from shoptools.abstractions.models import AbstractOrder, AbstractOrderLine
from shoptools.util import make_uuid


class FavouritesList(AbstractOrder):
    """
    Represents a list of favourites (or a wishlist), db persisted in the same
    manner as SavedCart. Items capable of being favourited are required to
    inherit from ICartItem.

    Each user can have multiple FavouritesLists, which can therefore optionally
    be named. Despite this, typically only a single list will need to be
    supported and get_favourites therefore returns the first (ie. most recent)
    FavouritesList. A specific FavouritesList can be altered by passing the
    get_favourites parameter to the relevant view.
    """
    created = models.DateTimeField(default=datetime.now)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    secret = models.UUIDField(editable=False, default=make_uuid, db_index=True)
    name = models.CharField(max_length=191, blank=True, default='')

    @property
    def total(self):
        return self.subtotal

    class Meta:
        ordering = ('-created', )

    def get_absolute_url(self):
        return reverse('favourites_favourites', args=(self.secret, ))

    def __str__(self):
        if self.name:
            return 'Favourites (%s) for %s' % (self.created,
                                               self.user.get_full_name())
        else:
            return 'Favourites (%s) for %s' % (self.name,
                                               self.user.get_full_name())

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


class FavouritesLine(AbstractOrderLine):
    parent_object = models.ForeignKey(FavouritesList, on_delete=models.CASCADE)
