import json

from django.http import HttpResponse
from django.conf import settings

from cart.cart import get_cart

if 'wishlist' in settings.INSTALLED_APPS:
    from wishlist.models import get_wishlist
else:
    get_wishlist = None

if 'regions' in settings.INSTALLED_APPS:
    from regions.util import regions_data
else:
    regions_data = None

if 'accounts' in settings.INSTALLED_APPS:
    from accounts.views import account_data
else:
    account_data = None


class JsonResponse(HttpResponse):
    def __init__(self, data):
        super(JsonResponse, self).__init__(json.dumps(data),
                                           content_type="application/json")


def get_data(request):
    """Collate user data from the different apps in use. """

    data = {
        'cart': get_cart(request).as_dict(),
    }

    if account_data:
        data['account'] = account_data(request)

    if get_wishlist:
        data['wishlist'] = get_wishlist(request).as_dict()

    if regions_data:
        data['regions'] = regions_data(request)

    return data


def get_data_view(request):
    return JsonResponse(get_data(request))
