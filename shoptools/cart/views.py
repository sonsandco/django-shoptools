import json

from django.http import HttpResponseRedirect, HttpResponse, \
    HttpResponseNotAllowed, HttpResponseBadRequest

from . import get_cart as default_get_cart
from . import actions
from . import signals


def cart_view(action=None):
    """Decorator supplies request and current cart as arguments to the action
       function. Returns appropriate errors if the request method is not POST,
       or if any required params are missing.
       Successful return value is either cart data as json, or a redirect, for
       ajax and non-ajax requests, respectively. """

    def view_func(request, next_url=None, get_cart=default_get_cart,
                  get_html_snippet=None):

        if action and not request.POST:
            return HttpResponseNotAllowed(['POST'])

        cart = get_cart(request)
        success = True

        post_params = request.POST.dict()

        # Remove next from POST parameters now if it was provided, as the
        # actions do not expect to receive it as an argument.
        if 'next' in post_params:
            if not next_url:
                next_url = post_params['next']
            del post_params['next']

        if action:
            # don't allow multiple values for each get param
            success, errors = action(post_params, cart)

            if success is None:
                return HttpResponseBadRequest()

        signal = getattr(signals, action.__name__, None)
        if signal:
            signal.send(
                sender=cart.__class__, success=success, request=request)

        if request.is_ajax():
            data = {
                'success': success,
                'errors': errors,
                'cart': cart.as_dict(),
            }
            if get_html_snippet:
                data['html_snippet'] = get_html_snippet(request, cart, errors)

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


# TODO rename - confusing
get_cart = cart_view()

all_actions = ('add', 'quantity', 'options', 'clear', 'set_voucher_codes')
for action in all_actions:
    locals()[action] = cart_view(getattr(actions, action))
