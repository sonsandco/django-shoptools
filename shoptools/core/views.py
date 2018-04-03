import json

from django.http import HttpResponse

from shoptools.cart import get_cart
from shoptools.util import \
    get_accounts_module, get_regions_module, get_favourites_module


accounts_module = get_accounts_module()
regions_module = get_regions_module()
favourites_module = get_favourites_module()


class JsonResponse(HttpResponse):
    def __init__(self, data):
        super(JsonResponse, self).__init__(json.dumps(data),
                                           content_type="application/json")


def get_data(request):
    """Collate user data from the different apps in use. """
    from django.apps import apps

    data = {}

    if apps.is_installed('shoptools.cart'):
        data['cart'] = get_cart(request).as_dict()

    if accounts_module:
        data['account'] = accounts_module.get_data(request)

    if favourites_module:
        data['favourites'] = favourites_module.get_data(request)

    if regions_module:
        data['regions'] = regions_module.get_data(request)

    return data


def get_data_view(request):
    return JsonResponse(get_data(request))
