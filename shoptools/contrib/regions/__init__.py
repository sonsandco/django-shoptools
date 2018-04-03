
def get_region(request):
    from .util import get_region
    return get_region(request)


def set_region(request):
    from .util import set_region
    return set_region(request)


def get_data(request):
    from .views import regions_data
    return regions_data(request)


def get_context(request):
    from .util import regions_context
    return regions_context(request)
