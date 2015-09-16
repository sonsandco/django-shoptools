from utilities.json_http import JsonResponse
from utilities.render import render

from wishlist.models import get_wishlist
from shop.views import get_recent_products


@render('accounts/orders.html')
def orders(request):
    return {}


@render('accounts/history.html')
def history(request):
    return {}


@render('accounts/details.html')
def details(request):
    return {}


@render('accounts/recent.html')
def recent(request):
    return {
        'products': get_recent_products(request),
    }


def account_data(request):
    account = {}

    # TODO include cart stuff here so only one call?

    if request.user.is_authenticated():
        account['user'] = {
            'first_name': request.user.first_name,
        }

    account['wishlist'] = get_wishlist(request).as_dict()

    return account


def account_data_view(request):
    return JsonResponse({'account': account_data(request)})
