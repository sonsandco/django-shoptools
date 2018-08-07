import json

from django.http import HttpResponseRedirect, HttpResponse, \
    HttpResponseNotAllowed, HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404, render
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.views.decorators.cache import never_cache

from shoptools.settings import FAVOURITES_SESSION_POST_KEY

from . import get_favourites as default_get_favourites
from . import actions
from .models import FavouritesList


@never_cache
def favourites(request, secret=None):
    if secret:
        favourites = get_object_or_404(FavouritesList, secret=secret)
    else:
        favourites = default_get_favourites(request)

    # If no secret was provided and the current user does not have favourites
    # (ie. not logged in and session carts not enabled), then redirect to login
    # / account creation.
    if not favourites:
        return redirect('login')

    return render(request, 'favourites/favourites.html', {
        'favourites': favourites
    })


def favourites_action_view(action=None):
    """
    Decorator supplies request and current favourites as arguments to the
    action function.

    Returns appropriate errors if the request method is not POST, or if any
    required params are missing.

    Successful return value is either favourites data as json, or a redirect,
    for ajax and non-ajax requests, respectively.

    Note: Although we support multiple FavouritesLists, default_get_favourites
    returns the first (ie. most recent) FavouritesList. If you wish to edit a
    specific FavouritesList, use the get_favourites parameter.
    """

    def view_func(request, next_url=None,
                  get_favourites=default_get_favourites,
                  get_html_snippet=None):

        if action and not request.POST:
            return HttpResponseNotAllowed(['POST'])

        favourites = get_favourites(request)
        post_params = request.POST.dict()

        # If the current user does not have favourites (ie. not logged in and
        # session carts not enabled), then redirect to login / account
        # creation.
        if not favourites:
            # Save post data to session so it will automatically be favourited
            # when the user logs in.
            # We only ever save one - assume if they didn't login after the
            # first time the attempted it then they must not have wanted to
            # add it.
            if action:
                post_params['action'] = action.__name__
                request.session[FAVOURITES_SESSION_POST_KEY] = post_params
                request.session.modified = True

            if request.is_ajax():
                data = {
                    'success': False,
                    'errors': 'Please login.',
                    'next': reverse('login')
                }
                return HttpResponse(json.dumps(data),
                                    content_type='application/json')
            else:
                return redirect('login')

        success = True

        # Remove next from POST parameters now if it was provided, as the
        # actions do not expect to receive it as an argument.
        if 'next' in post_params:
            if not next_url:
                next_url = post_params['next']
            del post_params['next']

        if action:
            # don't allow multiple values for each get param
            success, errors = action(post_params, favourites)

            if success is None:
                return HttpResponseBadRequest()

        if request.is_ajax():
            data = {
                'success': success,
                'errors': errors,
                'favourites': favourites.as_dict(),
            }
            if get_html_snippet:
                data['html_snippet'] = get_html_snippet(favourites, errors)

            return HttpResponse(json.dumps(data),
                                content_type='application/json')

        # TODO hook into messages framework here
        if success:
            if not next_url:
                next_url = request.META.get('HTTP_REFERER', '/')
            return HttpResponseRedirect(next_url)
        else:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    if action:
        view_func.__name__ = action.__name__
        view_func.__doc__ = action.__doc__
    return view_func


all_actions = ('add', 'quantity', 'options', 'clear', 'toggle')
for action in all_actions:
    locals()[action] = favourites_action_view(getattr(actions, action))
