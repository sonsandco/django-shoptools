from json import dumps

from django.http import HttpResponseRedirect, HttpResponse, \
HttpResponseBadRequest, HttpResponseNotAllowed
from django.core.urlresolvers import reverse
from django.template import RequestContext

from coffin.template.loader import get_template, TemplateNotFound

from .models import Cart
from . import actions


def cart_view(action=None):
    '''Decorator supplies request and current cart as arguments to the action 
       function. Returns appropriate errors if the request method is not POST,
       or if any required params are missing.
       Successful return value is either cart data as json, or a redirect, for
       ajax and non-ajax requests, respectively.'''
    
    def view_func(request, next=None):
        if action and request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])
        
        cart = Cart(request)
        if action:
            success = action(request, cart)
            
            if not success:
                return HttpResponseBadRequest(u"Invalid request")
        
        if request.is_ajax():
            cart_data = cart.as_dict()
            try:
                template = get_template('cart/cart_ajax.html')
            except TemplateNotFound:
                pass
            else:
                cart_data['html'] = template.render(RequestContext(request))
            
            return HttpResponse(dumps(cart_data), 
                                content_type="application/json")
        
        if not next:
            next = request.POST.get("next", request.META.get('HTTP_REFERER', '/'))
        return HttpResponseRedirect(next)
    
    if action:
        view_func.__name__ = action.__name__
        view_func.__doc__ = action.__doc__
    return view_func


get_cart = cart_view()
update_cart = cart_view(actions.update_cart)
add = cart_view(actions.add)
remove = cart_view(actions.remove)
clear = cart_view(actions.clear)

