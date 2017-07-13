
def get_region(request):
    from . import util
    return util.get_region(request)


def get_data(request):
    from .views import regions_data
    return regions_data(request)
