import json

from django.http import HttpResponseRedirect, HttpResponse, \
    HttpResponseNotAllowed, HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404, render
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required

from shoptools.settings import LOGIN_ADDITIONAL_POST_DATA_KEY

from . import actions
from .models import FavouritesList
from .util import favourites_data
from .forms import CreateFavouritesListForm


def favourites_action_view(action, allow_create=False):
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

    def view_func(request, next_url=None, get_html_snippet=None):

        if not request.POST:
            return HttpResponseNotAllowed(['POST'])

        post_params = request.POST.dict()

        # Remove next from POST parameters now if it was provided, as the
        # actions do not expect to receive it as an argument.
        if 'next' in post_params:
            if not next_url:
                next_url = post_params['next']
            del post_params['next']

        # Similarly for favourites_list_pk
        if 'favourites_list_pk' in post_params:
            favourites_list_pk = post_params['favourites_list_pk']
            del post_params['favourites_list_pk']
            try:
                favourites_list_pk = \
                    int(favourites_list_pk) if favourites_list_pk else None
            except ValueError:
                favourites_list_pk = None
        else:
            favourites_list_pk = None

        requires_login = False
        try:
            favourites = FavouritesList.objects.get(pk=favourites_list_pk)
        except FavouritesList.DoesNotExist:
            if allow_create and 'name' in post_params:
                if request.user.is_authenticated:
                    favourites = FavouritesList.objects.create(
                        name=post_params['name'],
                        user=request.user)
                    favourites.set_request(request)
                else:
                    requires_login = True
            else:
                return HttpResponseBadRequest()

        # Only allow actions if the favourites list belongs to current user
        if favourites and not favourites.user == request.user:
            requires_login = True

        if requires_login:
            # Save post data to session so the relevant action will be
            # automatically completed when the user logs in.
            post_params['app'] = __package__
            post_params['action'] = action.__name__
            request.session[LOGIN_ADDITIONAL_POST_DATA_KEY] = post_params
            request.session.modified = True

            if request.is_ajax():
                data = {
                    'success': False,
                    'errors': ['Please login.'],
                    'redirect_to': reverse('login'),
                    'next': next_url
                }
                return HttpResponse(json.dumps(data),
                                    content_type='application/json')
            else:
                return redirect(reverse('login') + '?next=' + next_url)

        success, errors = action(post_params, favourites)

        if success is None:
            return HttpResponseBadRequest()

        if request.is_ajax():
            data = {
                'success': success,
                'errors': errors,
                'favourites': favourites_data(request),
            }
            if get_html_snippet:
                data['html_snippet'] = \
                    get_html_snippet(request, favourites, errors)

            return HttpResponse(json.dumps(data),
                                content_type='application/json')

        # TODO hook into messages framework here
        if success:
            if not next_url:
                next_url = request.META.get('HTTP_REFERER', '/')
            return HttpResponseRedirect(next_url)
        else:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    view_func.__name__ = action.__name__
    view_func.__doc__ = action.__doc__
    return view_func


create = favourites_action_view(lambda post_params, favourites: (True, []),
                                allow_create=True)


actions_allow_create = ('add', )
for action in actions_allow_create:
    locals()[action] = favourites_action_view(getattr(actions, action),
                                              allow_create=True)


actions_require_existing = ('quantity', 'clear', 'remove', 'toggle',
                            'delete_favourites_list')
for action in actions_require_existing:
    locals()[action] = favourites_action_view(getattr(actions, action))


all_actions = actions_allow_create + actions_require_existing


def index(request):
    """
    Index is intended to be used as an introduction to the favourites system
    and explanation for the user of how it works. The default template is
    therefore very sparse since content will depend on your use case.

    The view is separated out from dashboard so that it can be cached.
    """
    return render(request, 'favourites/index.html', {
        'next': reverse('favourites_dashboard')
    })


@never_cache
@login_required
def dashboard(request):
    favourites = FavouritesList.objects.filter(user=request.user)
    favourites_form = CreateFavouritesListForm()

    return render(request, 'favourites/dashboard.html', {
        'favourites': favourites,
        'favourites_form': favourites_form,
        'next': reverse('favourites_dashboard')
    })


@never_cache
def detail(request, secret):
    favourites_list = get_object_or_404(FavouritesList, secret=secret)

    return render(request, 'favourites/detail.html', {
        'favourites_list': favourites_list,
        'editable': request.user == favourites_list.user
    })
