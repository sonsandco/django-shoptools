from django.template.loader import render_to_string

from shoptools.settings import FAVOURITES_SESSION_KEY


def get_favourites(request):
    from django.apps import apps

    session_favourites = None
    if apps.is_installed('shoptools.cart'):
        # If the cart is installed we support session level favourites.
        # Otherwise we only support favourites for logged in users.
        from shoptools.cart.session import SessionCart
        session_favourites = SessionCart(request, FAVOURITES_SESSION_KEY)

    if request.user.is_authenticated:
        # Django doesn't like this to be imported at compile-time if the
        # app is not installed
        from .models import FavouritesList

        # Default behaviour is to get the first (most recent) favourites list
        # for the logged in user
        favourites = FavouritesList.objects.filter(user=request.user).first()
        if not favourites:
            favourites = FavouritesList(user=request.user)

        favourites.set_request(request)

        # merge session favourites, if it exists
        if session_favourites and session_favourites.count():
            if not favourites.pk:
                favourites.save()
            session_favourites.save_to(favourites)
            session_favourites.clear()

        return favourites

    return session_favourites


def favourites_data(request):
    """Get region and country info from the session, as a dict for json
       serialization. """
    data = None

    favourites = get_favourites(request)
    if favourites:
        data = favourites.as_dict()

    return data


def get_html_snippet(favourites, errors=[]):
    return render_to_string('favourites/html_snippet.html', {
        'favourites': favourites,
        'favourites_errors': errors
    }, request=favourites.request)
