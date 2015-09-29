from json import dumps
from functools import partial
import importlib

from django.shortcuts import redirect, get_object_or_404
from django.template.loader import get_template
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.contrib.auth import authenticate, login

from cart.models import Cart, get_shipping_module
# from dps.transactions import make_payment
# from paypal.transactions import make_payment
from accounts.models import Account

from .models import Order, OrderLine
from .forms import OrderForm, CheckoutUserForm, GiftRecipientForm

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

    if request.user.is_authenticated():
        account = Account.objects.for_user(request.user)
        get_user_form = lambda *a: None
    else:
        account = Account()
        get_user_form = partial(CheckoutUserForm)

    if order:
        get_form = partial(OrderForm, instance=order)

        def sanity_check():
            return 0

        new_order = False
    else:
        # set initial data from the user's account, the shipping
        # options, and any saved session data
        initial = {}
        if account.pk and not initial:
            initial.update(account.as_dict())

        shipping_module = get_shipping_module()
        if shipping_module:
            initial.update(shipping_module.get_session(request))

        initial.update(request.session.get(CHECKOUT_SESSION_KEY, {}))

        get_form = partial(OrderForm, initial=initial)
        sanity_check = lambda: cart.subtotal
        new_order = True

    # Add in any custom cart verification here
    cart_errors = []

    if request.method == 'POST':
        form = get_form(request.POST, sanity_check=sanity_check())

        user_form = get_user_form(request.POST)
        save_details = not account.pk and request.POST.get('save-details')
        if save_details and user_form:
            # if creating a new user, the email needs to be unused
            form.require_unique_email = True
            user_form_valid = user_form.is_valid()
        else:
            user_form_valid = True

        gift_form = GiftRecipientForm(request.POST, prefix='gift')
        is_gift = request.POST.get('is_gift')
        gift_form_valid = gift_form.is_valid() if is_gift else True

        if form.is_valid() and (order or not cart.empty()) and \
           user_form_valid and gift_form_valid and not len(cart_errors):
            # save the order obj to the db...
            order = form.save(commit=False)
            order.currency = cart.currency

            # save details to account if requested
            if save_details:
                account.from_obj(order)
                if user_form:
                    user = user_form.save(email=order.email, name=order.name)
                    account.user = user
                    auth_user = authenticate(
                        username=user.email,
                        password=user_form.cleaned_data['password1'])
                    login(request, auth_user)
                account.save()

            if account.pk:
                order.account = account

            order.save()

            if is_gift:
                recipient = gift_form.save(commit=False)
                recipient.order = order
                recipient.save()

            if new_order:
                # save the cart to a series of orderlines
                cart.save_to(order, OrderLine)

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
        gift_form = GiftRecipientForm(prefix='gift')
        user_form = get_user_form()

    return {
        'form': form,
        'gift_form': gift_form,
        'user_form': user_form,
        'cart': cart,
        'order': order,
        'account': account,
        'cart_errors': cart_errors,
    }
