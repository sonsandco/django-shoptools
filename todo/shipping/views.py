# -*- coding: utf-8 -*-
import json

from django.http import HttpResponseBadRequest, HttpResponseRedirect, \
    HttpResponseNotAllowed, HttpResponse

from shoptools.cart import get_cart
from shoptools.cart.views import get_cart_html
from . import actions


def shipping_view(action=None):
    '''Decorator supplies request and current cart as arguments to the action
       function. Returns appropriate errors if the request method is not POST,
       or if any required params are missing.
       Successful return value is either cart data as json, or a redirect, for
       ajax and non-ajax requests, respectively.'''

    def view_func(request, next_url=None, data=None, get_cart=get_cart,
                  ajax_template='checkout/cart_ajax.html'):
        if not data:
            data = request.POST

        if action and not data:
            return HttpResponseNotAllowed(['POST'])

        cart = get_cart(request)
        cookie = None

        if action:
            # An empty dict signifies a failure to complete the update. None
            # signifies a bad request.
            new_dict, cookie = action(data, cart)
            if new_dict is None:
                return HttpResponseBadRequest("Invalid request")

        if request.is_ajax():
            data = {
                'success': bool(new_dict),
                'cart': cart.as_dict(),
            }
            if ajax_template:
                data['html_snippet'] = get_cart_html(request, cart,
                                                     ajax_template)
            response = HttpResponse(json.dumps(data),
                                    content_type="application/json")
            if cookie:
                cookie_name, cookie_value = cookie
                response.set_cookie(cookie_name, cookie_value)
            return response

        if not next_url:
            next_url = data.get('next', request.META.get('HTTP_REFERER', '/'))
        response = HttpResponseRedirect(next_url)
        if cookie:
            cookie_name, cookie_value = cookie
            response.set_cookie(cookie_name, cookie_value)
        return response

    if action:
        view_func.__name__ = action.__name__
        view_func.__doc__ = action.__doc__
    return view_func


all_actions = ('change_country', 'change_region', 'change_option')
for action in all_actions:
    locals()[action] = shipping_view(getattr(actions, action))
