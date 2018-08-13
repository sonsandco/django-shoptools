from django.template.loader import render_to_string


def get_all_favourites(request):
    favourites = []

    if request.user.is_authenticated:
        # Django doesn't like this to be imported at compile-time if the
        # app is not installed
        from .models import FavouritesList
        favourites = FavouritesList.objects.filter(user=request.user)
        return favourites

    return favourites


def favourites_data(request):
    """Get region and country info from the session, as a dict for json
       serialization. """
    data = []

    favourites_lists = get_all_favourites(request)
    for favourites_list in favourites_lists:
        data.append(favourites_list.as_dict())

    return data


def get_html_snippet(request, favourites_list, errors=[]):
    ctx = {
        'favourites_list': favourites_list,
        'favourites_errors': errors,
        'editable': request.user == favourites_list.user
    }
    return render_to_string('favourites/snippets/html_snippet.html', ctx,
                            request=request)
