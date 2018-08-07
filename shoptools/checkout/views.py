from functools import partial

from django.shortcuts import redirect, get_object_or_404, render
from django.http import Http404
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate, login
from django.contrib.admin.views.decorators import staff_member_required
# from django.contrib import messages

from shoptools.cart import get_cart
from shoptools.util import \
    get_accounts_module, get_shipping_module, get_regions_module, \
    get_vouchers_module, get_payment_module

from .forms import OrderForm, OrderMetaForm, CheckoutUserForm, AddressForm
from .models import Order, Address
from .emails import email_content
from .signals import checkout_pre_payment


CHECKOUT_SESSION_KEY = 'checkout-data'


def available_countries(cart):
    shipping_module = get_shipping_module()
    if shipping_module:
        return shipping_module.available_countries(cart)
    return None


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
    # Check for errors now, so if the cart is updated during this process it
    # is reflected in ctx.
    # TODO: rename error related methods to be validation related
    errors = cart.get_errors()

    ctx = {
        'cart': cart,
        'cart_errors': errors
    }

    region_module = get_regions_module()
    if region_module:
        context = region_module.get_context(request)
        if context:
            ctx.update(context)

    shipping_module = get_shipping_module()
    if shipping_module:
        context = shipping_module.get_context(cart)
        if context:
            ctx.update(context)

    vouchers_module = get_vouchers_module()
    if vouchers_module:
        context = vouchers_module.get_context(cart)
        if context:
            ctx.update(context)

    return render(request, 'checkout/cart.html', ctx)


@checkout_view
def checkout(request, cart, order=None):
    """Handle checkout process - if the order is completed, show the success
       page, otherwise show the checkout form.
    """

    if not order:
        # Don't simply put this as the default argument, see:
        # http://python-guide-pt-br.readthedocs.io/en/latest/writing/gotchas#mutable-default-arguments
        order = Order()
        new_order = True
    else:
        new_order = False

    # TODO should the checkout view only ever work with an Order, which may
    # be unsaved (created on the fly from the cart contents)?

    # if the cart is already linked with an (incomplete) order, show that order
    if not order.pk and cart.order_obj and \
            cart.order_obj.status < Order.STATUS_PAID:
        return redirect(cart.order_obj)

    # paid orders can't be edited, obvs
    # display the success page
    if order.pk and order.status >= Order.STATUS_PAID:
        if cart.order_obj == order:
            cart.clear()
        return order_success_response(request, order)

    # Send back to cart page if cart isn't valid. The cart view will show an
    # appropriate error message.
    # At this point we don't care about order.is_valid because its contents
    # will be overridden by the cart's contents anyway.
    if not cart.is_valid:
        return redirect('checkout_cart')

    # if the user is anon, and accounts module is installed, show
    # CheckoutUserForm so they can create an account
    accounts_module = get_accounts_module()
    accounts_enabled = bool(accounts_module)
    if accounts_enabled and not request.user.is_authenticated:
        get_user_form = partial(CheckoutUserForm, use_required_attribute=False,
                                prefix='checkout')
    else:
        def get_user_form(*args, **kwargs):
            return None

    if accounts_enabled:
        account = accounts_module.get_account(request.user)
    else:
        account = None

    # available countries for shipping
    shipping_countries = available_countries(cart)

    # get initial form data from the session, this may have been saved by a
    # previous form submission
    form_initial = request.session.get(CHECKOUT_SESSION_KEY, {})

    if new_order:
        get_order_form = partial(OrderForm, initial=form_initial)
    else:
        get_order_form = partial(OrderForm, instance=order)

    shipping_address = order.get_address(Address.TYPE_SHIPPING, True)
    billing_address = order.get_address(Address.TYPE_BILLING, True)

    # prefill shipping address from account, if a new order for an account
    if new_order and account and account.pk:
        shipping_address.from_obj(account)
        shipping_address.name = account.user.get_full_name()
        shipping_address.email = account.user.email
        shipping_address.address_type = Address.TYPE_SHIPPING

    get_shipping_form = partial(AddressForm, prefix='shipping',
                                instance=shipping_address,
                                initial=form_initial,
                                country_choices=shipping_countries)
    get_billing_form = partial(AddressForm, prefix='billing',
                               initial=form_initial,
                               use_required_attribute=False,
                               instance=billing_address)

    if request.method == 'POST':
        meta_form = OrderMetaForm(request.POST)
        # assume it's valid, because it's just BooleanFields
        meta_form.full_clean()
        save_details = meta_form.cleaned_data['save_details']
        billing_is_shipping = meta_form.cleaned_data['billing_is_shipping']

        order_form = get_order_form(request.POST)
        user_form = get_user_form(request.POST)
        shipping_form = get_shipping_form(request.POST)

        if save_details and user_form:
            # if saving details, the email needs to be unused
            shipping_form.require_unique_email = True
            user_form_valid = user_form.is_valid()
        else:
            user_form_valid = True

        if billing_is_shipping:
            billing_form = get_billing_form()
            billing_form_valid = True
        else:
            billing_form = get_billing_form(request.POST)
            billing_form_valid = billing_form.is_valid()

        if order_form.is_valid() and user_form_valid and \
                shipping_form.is_valid() and billing_form_valid:
            # save the order obj to the db...
            order = order_form.save(commit=False)
            code, symbol = cart.get_currency()
            order.currency_code = code
            order.currency_symbol = symbol

            # Collect shipping address values now in case we need to create an
            # account.
            shipping_address = shipping_form.save(commit=False)

            # save details to account if requested
            if save_details:
                account.from_obj(shipping_address)
                if user_form:
                    user = user_form.save(
                        email=shipping_address.email,
                        name=shipping_address.name)
                    account.user = user
                    auth_user = authenticate(
                        username=user.email,
                        password=user_form.cleaned_data['password1'])
                    login(request, auth_user)
                account.save()

            if request.user.is_authenticated:
                order.user = request.user

            order.save()

            shipping_address.order = order
            shipping_address.save()

            # only save the billing address if it's separate from shipping
            if not billing_is_shipping:
                billing_form.instance.order = order
                billing_form.save()

            if billing_is_shipping and order.get_address(Address.TYPE_BILLING):
                # edge case where the order was already saved with a separate
                # billing address - delete it
                order.billing_address.delete()

            # save any cart lines to the order, overwriting any existing lines
            cart.save_to(order)

            # and off we go to pay, if necessary
            payment_module = get_payment_module()
            checkout_pre_payment.send(sender=Order, request=request)
            if order.total <= 0:
                order.transaction_succeeded()
                return redirect(order)
            else:
                if payment_module:
                    return payment_module.make_payment(order, request)
                else:
                    order.transaction_failed()
                    return redirect(order)
        else:
            # Save posted data so the user doesn't have to re-enter it
            request.session[CHECKOUT_SESSION_KEY] = request.POST.dict()
            request.session.modified = True
    else:
        meta_form = OrderMetaForm()
        order_form = get_order_form()
        shipping_form = get_shipping_form()
        billing_form = get_billing_form()
        user_form = get_user_form()

    ctx = {
        'order_form': order_form,
        'meta_form': meta_form,
        'shipping_form': shipping_form,
        'billing_form': billing_form,
        'user_form': user_form,
        'cart': cart,
        'order': order,
        'accounts_enabled': accounts_enabled,
        'account': account
    }

    region_module = get_regions_module()
    if region_module:
        context = region_module.get_context(request)
        if context:
            ctx.update(context)

    shipping_module = get_shipping_module()
    if shipping_module:
        context = shipping_module.get_context(cart)
        if context:
            ctx.update(context)

    vouchers_module = get_vouchers_module()
    if vouchers_module:
        context = vouchers_module.get_context(cart)
        if context:
            ctx.update(context)

    return render(request, 'checkout/checkout.html', ctx)


def order_success_response(request, order):
    first_view = not order.success_page_viewed
    if first_view:
        order.success_page_viewed = True
        order.save()

    ctx = {
        'order': order,
        'first_view': first_view,
    }

    vouchers_module = get_vouchers_module()
    if vouchers_module:
        context = vouchers_module.get_context(cart)
        if context:
            ctx.update(context)

    return render(request, 'checkout/success.html', ctx)


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
    emails = []
    for t in ('receipt', 'notification', 'dispatch'):
        emails.append(email_content(t, order=order))

    return render(request, 'checkout/preview_emails.html', {
        'emails': emails,
    })


@staff_member_required
def preview_first_emails(request):
    order = Order.objects.first()
    return redirect(preview_emails, order.secret)
