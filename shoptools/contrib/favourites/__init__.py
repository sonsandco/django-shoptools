
def get_favourites(request):
    from .util import get_favourites
    return get_favourites(request)


def get_data(request):
    from .util import favourites_data
    return favourites_data(request)
