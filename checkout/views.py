from functools import partial
import importlib

from django.shortcuts import redirect, get_object_or_404, render
from django.http import Http404
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

from cart.cart import get_cart
from accounts.models import Account

from .forms import OrderForm, CheckoutUserForm, GiftRecipientForm
from .models import Order
from .emails import email_content


CHECKOUT_SESSION_KEY = 'checkout-data'
PAYMENT_MODULE = getattr(settings, 'CHECKOUT_PAYMENT_MODULE', None)


def get_payment_module():
    return importlib.import_module(PAYMENT_MODULE) if PAYMENT_MODULE else None


def with_order(wrapped_view):
    """Supplies order object to wrapped view function based on secret. """

    @never_cache
    def view_func(request, secret, **kwargs):
        order = get_object_or_404(Order, secret=secret)

        # prevent non-staff from viewing other people's orders
        if order.user and not request.user.is_staff and order and \
                order.user != request.user:
            return redirect(reverse('login') + '?next=' + request.path_info)

        return wrapped_view(request, order=order, **kwargs)

    view_func.__name__ = wrapped_view.__name__
    view_func.__doc__ = wrapped_view.__doc__
    return view_func


def checkout_view(view):
    """Supplies current cart and optional order (if a secret is passed) to
       wrapped view function. """

    @never_cache
    def view_func(request, secret=None):
        cart = get_cart(request)

        # TODO simplify this by just passing through one "order obj", which may
        # be an order or a cart, rather than both. This should be possible
        # since they share an interface. Will require some view rearranging
        # though
        if secret:
            # wrap in with_order so the secret will be converted to an order
            wrapped_view = partial(with_order(view), secret=secret)
        else:
            wrapped_view = view

        return wrapped_view(request, cart=cart)

    view_func.__name__ = view.__name__
    view_func.__doc__ = view.__doc__
    return view_func


@checkout_view
def cart(request, cart, order=None):
    for error in cart.get_errors():
        messages.add_message(request, messages.ERROR, error)
    return render(request, 'checkout/cart.html', {
        'cart': cart,
    })


@checkout_view
def checkout(request, cart, order=None):
    """Handle checkout process - if the order is completed, show the success
       page, otherwise show the checkout form.
    """

    # if the cart is already linked with an (incomplete) order, show that order
    if not order and cart.order_obj and \
       cart.order_obj.status < Order.STATUS_PAID:
        return redirect(cart.order_obj)

    # paid orders can't be edited, obvs
    if order and order.status >= Order.STATUS_PAID:
        if cart.order_obj == order:
            cart.clear()

        display_tracking = False
        if not order.tracking_displayed:
            display_tracking = True
            order.tracking_displayed = True
            order.save()

        return render(request, 'checkout/success.html', {
            'order': order,
            "display_tracking": display_tracking,
        })

    # TODO review this. If there's any errors, we need to send back to the
    # cart, but if it's a saved order the cart may not
    # match. Possibly in this edge case we overwrite the cart with the order's
    # lines first?

    # TODO should the checkout view only ever work with an Order, which may
    # be unsaved (created on the fly from the cart contents)

    # Send back to cart page if cart isn't valid. The cart view will show an
    # appropriate error message
    valid = (order or cart).is_valid
    if not valid:
        return redirect('checkout_cart')

    # if the user is anon, show CheckoutUserForm so they can create an account
    if request.user.is_authenticated:
        account = Account.objects.for_user(request.user)

        def get_user_form(*args):
            return None
    else:
        account = Account()
        get_user_form = partial(CheckoutUserForm)

    if order:
        get_order_form = partial(OrderForm, instance=order, cart=cart,
                                 # TODO review - do we need a sanity check
                                 # here?
                                 sanity_check=order.subtotal)
        get_shipping_form = partial(ShippingAddressForm, prefix='shipping',
                                    instance=order.get_shipping_address(True),
                                    cart=cart)
        get_billing_form = partial(BillingAddressForm, prefix='billing',
                                   instance=order.get_billing_address(True))

        new_order = False
    else:
        # set initial data from the user's account, the shipping
        # options, and any saved session data
        address_initial = {}
        if account.pk and not address_initial:
            address_initial.update(account.as_dict())

        order_initial = {}
        order_initial.update(cart.get_shipping_options())
        order_initial.update(request.session.get(CHECKOUT_SESSION_KEY, {}))

        get_order_form = partial(OrderForm, initial=order_initial, cart=cart,
                                 sanity_check=cart.subtotal)
        get_shipping_form = partial(ShippingAddressForm, prefix='shipping',
                                    initial=address_initial, cart=cart)
        get_billing_form = partial(BillingAddressForm, prefix='billing')

        new_order = True

    use_shipping_address = True
    if request.method == 'POST':
        is_gift = request.POST.get('is_gift', False)

        order_form = get_order_form(request.POST)

        # get_user_form may returns None if the user is logged in
        user_form = get_user_form(request.POST)
        save_details = request.POST.get('save_details')
        if save_details and user_form:
            # if saving details, the email needs to be unused
            order_form.require_unique_email = True
            user_form_valid = user_form.is_valid()
        else:
            user_form_valid = True

        shipping_form = get_shipping_form(request.POST)
        use_shipping_address = request.POST.get('use_shipping_address', False)
        if use_shipping_address:
            billing_form = get_billing_form()
            billing_form_valid = True
        else:
            billing_form = get_billing_form(request.POST)
            billing_form_valid = billing_form.is_valid()

        shipping_form_valid = shipping_form.is_valid()

        if order_form.is_valid() and (order or not cart.empty()) and \
                user_form_valid and shipping_form_valid and billing_form_valid:
            # save the order obj to the db...
            order = order_form.save(commit=False)
            # order.currency = cart.currency

            # TODO make this configurable - don't rely on the region app being
            # present. Also need to determine currency at cart level, and
            # use it to calculate prices
            from regions.util import get_region
            region = get_region(request)
            order.currency = region.currency

            # save details to account if requested
            if save_details:
                account.from_obj(order)
                if user_form:
                    user = user_form.save(
                        email=order.get_billing_address().email,
                        name=order.get_billing_address().name)
                    account.user = user
                    auth_user = authenticate(
                        username=user.email,
                        password=user_form.cleaned_data['password1'])
                    login(request, auth_user)
                account.save()

            if request.user.is_authenticated:
                order.user = request.user

            order.save()

            shipping_address = shipping_form.save(commit=False)
            shipping_address.order = order
            shipping_address.save()

            if use_shipping_address:
                billing_address = BillingAddress(**shipping_address.to_dict())
            else:
                billing_address = billing_form.save(commit=False)
            billing_address.order = order
            billing_address.save()

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
        is_gift = request.POST.get('is_gift', False)
        order_form = get_order_form()
        shipping_form = get_shipping_form()
        billing_form = get_billing_form()
        user_form = get_user_form()

    return render(request, 'checkout/checkout.html', {
        'template': 'checkout/checkout.html',
        'order_form': order_form,
        'shipping_form': shipping_form,
        'billing_form': billing_form,
        'user_form': user_form,
        'cart': cart,
        'order': order,
        'account': account,
        'use_shipping_address': use_shipping_address,
        'is_gift': is_gift
    }


@with_order
def invoice(request, order):
    if order.status < order.STATUS_PAID:
        raise Http404

    return render(request, 'checkout/invoice.html', {
        'order': order,
    })


@staff_member_required
@with_order
def preview_emails(request, order):
    # send_email('receipt', [order.email], order=order)
    # send_email('notification', [t[1] for t in settings.CHECKOUT_MANAGERS],
    #            order=order)
    emails = []
    for t in ('receipt', 'notification', 'dispatch'):
        emails.append(email_content(t, order=order))

    return render(request, 'checkout/preview_emails.html', {
        'emails': emails,
    })
