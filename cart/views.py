import json

from django.http import HttpResponseRedirect, HttpResponse, \
    HttpResponseBadRequest, HttpResponseNotAllowed
from django.template.loader import get_template, TemplateDoesNotExist

from . import cart
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

    def view_func(request, next_url=None, data=None, get_cart=cart.get_cart,
                  ajax_template='checkout/cart_ajax.html'):
        if not data:
            data = request.POST

        if action and not data:
            return HttpResponseNotAllowed(['POST'])

        cart = get_cart(request)
        if action:
            success = action(data, cart)
            if not success:
                return HttpResponseBadRequest(u"Invalid request")

        if request.is_ajax():
            data = {
                'cart': cart.as_dict(),
            }
            if ajax_template:
                data['html_snippet'] = get_cart_html(request, cart,
                                                     ajax_template)
            return HttpResponse(json.dumps(data),
                                content_type="application/json")

        if not next_url:
            next_url = request.POST.get("next",
                                        request.META.get('HTTP_REFERER', '/'))
        return HttpResponseRedirect(next_url)

    if action:
        view_func.__name__ = action.__name__
        view_func.__doc__ = action.__doc__
    return view_func


# TODO rename - confusing
get_cart = cart_view()

all_actions = ('update_cart', 'add', 'quantity', 'clear',
               # 'update_shipping',
               'update_vouchers')
for action in all_actions:
    locals()[action] = cart_view(getattr(actions, action))
