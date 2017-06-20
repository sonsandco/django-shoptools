from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login

from utilities.render import render

from shoptools.checkout.models import Order
# from shoptools.cart import get_cart

from .models import Account
from .forms import AccountForm, UserForm, CreateUserForm


@login_required
@render('accounts/orders.html')
def orders(request):
    account = Account.objects.for_user(request.user)
    orders = Order.objects.filter(user=account.user)
    current = orders.filter(status=Order.STATUS_PAID) \
                    .order_by('created')
    completed = orders.filter(status=Order.STATUS_SHIPPED) \
                      .order_by('-created')

    return {
        'orders': orders,
        'current': current,
        'completed': completed,
    }


@login_required
@render('accounts/details.html')
def details(request):
    account = Account.objects.for_user(request.user)

    if request.method == 'POST':
        account_form = AccountForm(request.POST, instance=account)
        user_form = UserForm(request.POST, instance=account.user)
        if account_form.is_valid() and user_form.is_valid():
            account_form.save()
            user_form.save()
            messages.info(request, 'Your details were saved')
            return redirect(details)
    else:
        account_form = AccountForm(instance=account)
        user_form = UserForm(instance=account.user)

    return {
        'account_form': account_form,
        'user_form': user_form,
    }


@render('accounts/create.html')
def create(request):
    initial = {}

    # cart = get_cart(request)
    # initial.update(cart.get_shipping_options())

    if request.method == 'POST':
        account_form = AccountForm(request.POST, initial=initial)
        user_form = CreateUserForm(request.POST)
        if account_form.is_valid() and user_form.is_valid():
            account = account_form.save(commit=False)
            account.user = user_form.save()
            account.save()
            auth_user = authenticate(
                username=account.user.username,
                password=user_form.cleaned_data['password1'])
            login(request, auth_user)
            messages.info(request, 'Your account was created.')
            return redirect(details)
    else:
        account_form = AccountForm(initial=initial)
        user_form = CreateUserForm()

    return {
        'account_form': account_form,
        'user_form': user_form,
    }


def account_data(request):
    data = None

    if request.user.is_authenticated:
        data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        }

    return data
