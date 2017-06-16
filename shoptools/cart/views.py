import json

from django.http import HttpResponseRedirect, HttpResponse, \
    HttpResponseNotAllowed, HttpResponseBadRequest

from . import get_cart as default_get_cart
from . import actions
from .util import get_cart_html


def cart_view(action=None):
    """Decorator supplies request and current cart as arguments to the action
       function. Returns appropriate errors if the request method is not POST,
       or if any required params are missing.
       Successful return value is either cart data as json, or a redirect, for
       ajax and non-ajax requests, respectively. """

    def view_func(request, next_url=None, get_cart=default_get_cart,
                  ajax_template=None):

        if action and not request.POST:
            return HttpResponseNotAllowed(['POST'])

        cart = get_cart(request)
        success = True
        if action:
            # don't allow multiple values for each get param
            success, errors = action(request.POST.dict(), cart)

            if success is None:
                return HttpResponseBadRequest()

            # TODO remove this, since shipping validation happens in
            # cart.get_errors
            # if success:
            #     # Update shipping since country, quantity etc may have changed
            #     shipping_module = get_shipping_module()
            #     if shipping_module:
            #         shipping_module.save_to_cart(cart, **cart.get_shipping_options())

        if request.is_ajax():
            data = {
                'success': success,
                'errors': errors,
                'cart': cart.as_dict(),
            }
            if ajax_template:
                data['html_snippet'] = get_cart_html(cart, ajax_template)

            return HttpResponse(json.dumps(data),
                                content_type='application/json')

        # TODO hook into messages framework here
        if success:
            if not next_url:
                next_url = request.POST.get(
                    'next', request.META.get('HTTP_REFERER', '/'))
            return HttpResponseRedirect(next_url)
        else:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    if action:
        view_func.__name__ = action.__name__
        view_func.__doc__ = action.__doc__
    return view_func


# TODO rename - confusing
get_cart = cart_view()

all_actions = ('add', 'quantity', 'clear',
               'set_shipping_options', 'set_voucher_codes')
for action in all_actions:
    locals()[action] = cart_view(getattr(actions, action))
