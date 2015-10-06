from json import dumps
from functools import partial
import importlib

from django.shortcuts import redirect, get_object_or_404
from django.template.loader import get_template
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.conf import settings

from cart.models import Cart
# from dps.transactions import make_payment
# from paypal.transactions import make_payment

from .forms import OrderForm
from .models import Order, OrderLine

CHECKOUT_SESSION_KEY = 'checkout-data'
PAYMENT_MODULE = getattr(settings, 'CHECKOUT_PAYMENT_MODULE', None)


def get_payment_module():
    return importlib.import_module(PAYMENT_MODULE) if PAYMENT_MODULE else None


def checkout_view(wrapped_view):
    '''Supplies request and current cart to wrapped view function, and returns
       partial html response for ajax requests. Assumes template filename
       corresponds to the view function name, unless template is provided
       by the view.'''

    @never_cache
    def view_func(request, secret=None):
        cart = Cart(request)
        if secret:
            order = get_object_or_404(Order, secret=secret)
        else:
            order = None
        ctx = {'request': request, 'cart': cart}
        result = wrapped_view(request, cart, order)

        if isinstance(result, HttpResponseRedirect):
            if request.is_ajax() and (result.url.startswith('http://') or
                                      result.url.startswith('https://')):
                return HttpResponse(dumps({'url': result.url}),
                                    content_type="application/json")
            else:
                return result

        elif isinstance(result, dict):
            ctx.update(result)

        template = result.get('template', wrapped_view.__name__)
        if request.is_ajax():
            template_name = 'checkout/%s_ajax.html' % template
        else:
            template_name = 'checkout/%s.html' % template

        content = get_template(template_name).render(ctx, request=request)
        return HttpResponse(content)

    view_func.__name__ = wrapped_view.__name__
    view_func.__doc__ = wrapped_view.__doc__
    return view_func


@checkout_view
def cart(request, cart, order):
    return {}


@checkout_view
def checkout(request, cart, order):
    """Handle checkout process - if the order is completed, show the success
       page, otherwise show the checkout form.
    """

    if order and order.status >= Order.STATUS_PAID:
        return {
            "template": "success",
            "order": order,
        }

    else:

    if order:
        get_form = partial(OrderForm, instance=order)

        def sanity_check():
            return 0

        new_order = False
    else:
        # if any shipping options match form fields, prefill them
        initial = request.session.get(CHECKOUT_SESSION_KEY,
                                      cart.get_shipping_options())
        get_form = partial(OrderForm, initial=initial)
        sanity_check = lambda: cart.subtotal
        new_order = True

    # Add in any custom cart verification here
    cart_errors = []

    if request.method == 'POST':
        form = get_form(request.POST, sanity_check=sanity_check())

        if form.is_valid() and (order or not cart.empty()) and \
           not len(cart_errors):
            # save the order obj to the db...
            order = form.save(commit=False)
            order.currency = cart.currency
            order.save()

            if new_order:
                # save the cart to a series of orderlines
                cart.save_to(order)

                # save shipping info
                order.shipping_options = cart.shipping_options
                order.shipping_cost = cart.shipping_cost
                order.save()

                cart.clear()

            # and off we go to pay, if necessary
            if order.total:
                return get_payment_module().make_payment(order, request)
            else:
                order.transaction_succeeded()
                return redirect(order)
        else:
            # Save posted data so the user doesn't have to re-enter it
            request.session[CHECKOUT_SESSION_KEY] = request.POST.dict()
            request.session.modified = True
    else:
        form = get_form(sanity_check=sanity_check())

    return {
        'form': form,
        'cart': cart,
        'order': order,
        'cart_errors': cart_errors,
    }
