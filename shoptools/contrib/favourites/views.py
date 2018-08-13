import json

from django.http import HttpResponseRedirect, HttpResponse, \
    HttpResponseNotAllowed, HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404, render
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.views.decorators.cache import never_cache

from shoptools.settings import LOGIN_ADDITIONAL_POST_DATA_KEY

from . import actions
from .models import FavouritesList
from .util import favourites_data
from .forms import CreateFavouritesListForm


def favourites_action_view(action):
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
        else:
            favourites_list_pk = None

        try:
            favourites = FavouritesList.objects.get(pk=favourites_list_pk)
        except FavouritesList.DoesNotExist:
            return HttpResponseBadRequest()

        # Only allow actions if the favourites list belongs to current user
        if favourites and not favourites.user == request.user:
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


all_actions = ('add', 'quantity', 'clear', 'toggle')
for action in all_actions:
    locals()[action] = favourites_action_view(getattr(actions, action))


@never_cache
def index(request):
    if request.user.is_authenticated:
        favourites = FavouritesList.objects.filter(user=request.user)
    else:
        favourites = []

    return render(request, 'favourites/index.html', {
        'favourites': favourites,
        'next': reverse('favourites_index')
    })


@never_cache
def detail(request, secret):
    favourites_list = get_object_or_404(FavouritesList, secret=secret)

    return render(request, 'favourites/detail.html', {
        'favourites_list': favourites_list,
        'editable': request.user == favourites_list.user
    })


@never_cache
def create(request):
    if request.POST:
        favourites_form = CreateFavouritesListForm(request.POST)
        next_url = request.POST.get('next', '')

        if favourites_form.is_valid():
            favourites_list = favourites_form.save(commit=False)
            favourites_list.set_request(request)
            favourites_list.user = request.user
            favourites_list.save()

            if request.is_ajax():
                data = {
                    'success': True,
                    'errors': [],
                    'favourites': favourites_data(request),
                }

                return HttpResponse(json.dumps(data),
                                    content_type='application/json')

            if not next_url:
                next_url = request.META.get('HTTP_REFERER',
                                            reverse('favourites_index'))
            return HttpResponseRedirect(next_url)
    else:
        next_url = request.GET.get('next', reverse('favourites_index'))
        favourites_form = CreateFavouritesListForm()

    ctx = {
        'favourites_form': favourites_form,
        'next': next_url
    }

    return render(request, 'favourites/create.html', ctx)
