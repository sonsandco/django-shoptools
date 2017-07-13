import json

from django.http import HttpResponse
from django.conf import settings

from shoptools.cart import get_cart
from shoptools.cart.util import get_accounts_module, get_regions_module


accounts_module = get_accounts_module()
regions_module = get_regions_module()


# TODO need a smarter way to do this - extra apps should somehow register their
# presence with the shoptools core
if 'wishlist' in settings.INSTALLED_APPS:
    from wishlist.models import get_wishlist
else:
    get_wishlist = None


class JsonResponse(HttpResponse):
    def __init__(self, data):
        super(JsonResponse, self).__init__(json.dumps(data),
                                           content_type="application/json")


def get_data(request):
    """Collate user data from the different apps in use. """

    data = {
        'cart': get_cart(request).as_dict(),
    }

    if accounts_module:
        data['account'] = accounts_module.get_data(request)

    if get_wishlist:
        data['wishlist'] = get_wishlist(request).as_dict()

    if regions_module:
        data['regions'] = regions_module.get_data(request)

    return data


def get_data_view(request):
    return JsonResponse(get_data(request))
