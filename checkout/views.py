from json import dumps
from functools import partial

from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache

from cart.models import Cart
from cart.actions import update_cart
# from dps.transactions import make_payment
from paypal.transactions import make_payment

from .renderer import renderer_factory
from .forms import OrderForm
from .models import Order

CHECKOUT_SESSION_KEY = 'checkout-data'


def checkout_view(wrapped_view):
    '''Supplies request and current cart to wrapped view function, and returns
       partial html response for ajax requests. Assumes template filename 
       corresponds to the view function name.'''
    
    @never_cache
    def view_func(request, *args):
        cart = Cart(request)
        ctx = {'cart': cart}
        result = wrapped_view(request, cart, *args)
        
        if isinstance(result, HttpResponseRedirect):
            if request.is_ajax() and (result.url.startswith('http://') or
                                      result.url.startswith('https://')):
                return HttpResponse(dumps({'url': result.url}), 
                                    content_type="application/json")
            else:
                return result
        
        elif isinstance(result, dict):
            ctx.update(result)
        
        if request.is_ajax():
            template = 'checkout/%s_ajax.html' % wrapped_view.__name__
        else:
            template = 'checkout/%s.html' % wrapped_view.__name__
            
        return renderer_factory()(template, RequestContext(request, ctx))
    
    view_func.__name__ = wrapped_view.__name__
    view_func.__doc__ = wrapped_view.__doc__
    return view_func


@checkout_view
def cart(request, cart):
    pass
    # if request.method == 'POST':
    #     # Delegate to cart's update view on post
    #     
    #     if request.POST.get('confirm'):
    #         next = reverse(checkout)
    #     else:
    #         next = reverse(cart)
    #     
    #     return update_cart(request, next)
    


@checkout_view
def checkout(request, cart, secret=None):
    if secret:
        order = get_object_or_404(Order, secret=secret)
        if order.status in [Order.STATUS_PAID, Order.STATUS_SHIPPED]:
            return redirect(success, secret)
        get_form = partial(OrderForm, instance=order)
        sanity_check = lambda: 0
        new_order = False
    else:
        order = None
        initial = request.session.get(CHECKOUT_SESSION_KEY, {})
        get_form = partial(OrderForm, initial=initial)
        sanity_check = cart.total
        new_order = True
    
    submitted = request.method == 'POST' and request.POST.get('form')
    
    if submitted == 'cart':
        update_cart(request, cart)
    
    cart_errors = []

    if submitted == 'checkout':
        form = get_form(request.POST, sanity_check=sanity_check())
        
        if cart.count() < 12:
            cart_errors.append(u'Minimum order 12 bottles')
        
        if form.is_valid() and (order or not cart.empty()) and \
           not len(cart_errors):
            # save the order obj to the db...
            order = form.save(commit=False)
            order.currency = cart.currency
            order.save()
            
            if new_order:
                # save the cart to a series of orderlines for it
                cart.save_to(order)
                cart.clear()
            
            # and off we go to pay
            return make_payment(order, request)
        else:
            # Save posted data so the user doesn't have to re-enter it
            request.session[CHECKOUT_SESSION_KEY] = request.POST.dict()
            request.session.modified = True
    else:
        form = get_form(sanity_check=sanity_check())
    
    return {
        "form": form,
        "cart": cart,
        "order": order,
        'cart_errors': cart_errors,
    }


@checkout_view
def success(request, cart, secret):
    qs = Order.objects.filter(status__in=[Order.STATUS_PAID,
                                          Order.STATUS_SHIPPED])
    order = get_object_or_404(Order, secret=secret)
    
    return {
        "order": order,
    }
    



