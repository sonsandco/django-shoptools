import json

from django.http import HttpResponseRedirect, HttpResponse, \
    HttpResponseBadRequest, HttpResponseNotAllowed
from django.template.loader import get_template, TemplateDoesNotExist

from .cart import get_cart as default_get_cart
from . import actions


def get_cart_html(request, cart, template_name):
    try:
        template = get_template(template_name)
    except TemplateDoesNotExist:
        return None
    else:
        return template.render({'cart': cart}, request=request)


def cart_view(action=None):
    '''Decorator supplies request and current cart as arguments to the action
       function. Returns appropriate errors if the request method is not POST,
       or if any required params are missing.
       Successful return value is either cart data as json, or a redirect, for
       ajax and non-ajax requests, respectively.'''

    def view_func(request, next_url=None, data=None, get_cart=default_get_cart,
                  ajax_template='checkout/cart_ajax.html'):
        if not data:
            data = request.POST

        if action and not data:
            return HttpResponseNotAllowed(['POST'])

        cart = get_cart(request)
        success = True
        if action:
            # success is a nulleable boolean, None = InvalidRequest,
            # False = failure, True = success
            success = action(data, cart)
            if success is None:
                return HttpResponseBadRequest('Invalid request')

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
                'cart': cart.as_dict()
            }
            if ajax_template:
                data['html_snippet'] = get_cart_html(request, cart,
                                                     ajax_template)
            return HttpResponse(json.dumps(data),
                                content_type='application/json')

        if success:
            if not next_url:
                next_url = data.get('next',
                                    request.META.get('HTTP_REFERER', '/'))
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
               'set_shipping_options', )
for action in all_actions:
    locals()[action] = cart_view(getattr(actions, action))
