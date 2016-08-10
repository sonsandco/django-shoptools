from json import dumps
from functools import partial
import importlib

from django.shortcuts import redirect, get_object_or_404
from django.template.loader import get_template
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.admin.views.decorators import staff_member_required

from cart.cart import get_cart
# from dps.transactions import make_payment
# from paypal.transactions import make_payment
from accounts.models import Account

from .forms import OrderForm, CheckoutUserForm, GiftRecipientForm
from .models import Order
from .emails import email_content

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
        cart = get_cart(request)

        # TODO simplify this by just passing through one "order obj", which may
        # be an order or a cart, rather than both. This should be possible
        # since they share an interface. Will require some view rearranging
        # though
        if secret:
            order = get_object_or_404(Order, secret=secret)
        else:
            order = None

        # Prevent going past the cart page if shipping is not valid, unless
        # this an order that has already been paid
        if not order or order.status < order.STATUS_PAID:
            if not cart.has_valid_shipping:
                cart_url = reverse('checkout_cart')
                if request.path_info != cart_url:
                    return redirect(cart_url)

        if order and order.user and order.user != request.user and \
           not request.user.is_staff:
            return redirect(reverse('login') + '?next=' + request.path_info)

        ctx = {'request': request, 'cart': cart}
        result = wrapped_view(request, cart, order)

        if isinstance(result, HttpResponseRedirect):
            if request.is_ajax() and (result.url.startswith('http://') or
                                      result.url.startswith('https://')):
                return HttpResponse(dumps({'url': result.url}),
                                    content_type="application/json")
            else:
                return result
        elif isinstance(result, HttpResponse):
            return result
        elif isinstance(result, dict):
            # TODO make this an else, we should assume it's a dict
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

    # if the cart is already linked with an (incomplete) order, show that order
    if not order and cart.order_obj and \
       cart.order_obj.status < Order.STATUS_PAID:
        return redirect(cart.order_obj)

    if order and order.status >= Order.STATUS_PAID:
        if cart.order_obj == order:
            cart.clear()
        return {
            "template": "success",
            "order": order
        }

    if request.user.is_authenticated():
        account = Account.objects.for_user(request.user)
        get_user_form = lambda *a: None
    else:
        account = Account()
        get_user_form = partial(CheckoutUserForm)

    if order:
        get_form = partial(OrderForm, instance=order)
        get_gift_form = partial(GiftRecipientForm, prefix='gift',
                                instance=order.get_gift_recipient())

        def sanity_check():
            return 0

        new_order = False
    else:
        # set initial data from the user's account, the shipping
        # options, and any saved session data
        initial = {}
        if account.pk and not initial:
            initial.update(account.as_dict())

        initial.update(cart.get_shipping())
        initial.update(request.session.get(CHECKOUT_SESSION_KEY, {}))

        get_form = partial(OrderForm, initial=initial)
        get_gift_form = partial(GiftRecipientForm, prefix='gift')
        sanity_check = lambda: cart.subtotal
        new_order = True

    # Verify the order (stock levels etc should be picked up here)
    cart_errors = (order or cart).get_errors()

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

        gift_form = get_gift_form(request.POST)
        is_gift = request.POST.get('is-gift')
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
                order.user = account.user

            order.save()

            if is_gift:
                recipient = gift_form.save(commit=False)
                recipient.order = order
                recipient.save()
            elif gift_form.instance and gift_form.instance.pk:
                gift_form.instance.delete()

            # save any cart lines to the order, overwriting existing lines, but
            # only if the order is either new, or matches the cart
            if not cart.empty() and (new_order or cart.order_obj == order):
                cart.save_to(order)

            # and off we go to pay, if necessary
            if order.total > 0:
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
        gift_form = get_gift_form()
        user_form = get_user_form()

    if order:
        shipping = order.get_shipping()
    else:
        shipping = cart.get_shipping()
    selected_country = None
    valid_countries = None
    region = shipping.get('region', None)
    if region:
        # if we found a region then this can't be basic shipping
        from shipping.models import Region
        selected_country = shipping.get('country', None)
        region = Region.objects.get(id=region)
        valid_countries = \
            [(c.code, c.name) for c in region.countries.all()]

    return {
        'form': form,
        'gift_form': gift_form,
        'user_form': user_form,
        'cart': cart,
        'order': order,
        'account': account,
        'cart_errors': cart_errors,
        'valid_countries': valid_countries,
        'selected_country': selected_country
    }


@checkout_view
def invoice(request, cart, order):
    if order.status < order.STATUS_PAID:
        raise Http404

    content = get_template('checkout/invoice.html').render({
        'order': order,
    }, request=request)
    return HttpResponse(content)


@staff_member_required
@checkout_view
def preview_emails(request, cart, order):
    # send_email('receipt', [order.email], order=order)
    # send_email('notification', [t[1] for t in settings.CHECKOUT_MANAGERS],
    #            order=order)
    emails = []
    for t in ('receipt', 'notification', 'dispatch'):
        emails.append(email_content(t, order=order))

    return {
        'emails': emails,
    }
