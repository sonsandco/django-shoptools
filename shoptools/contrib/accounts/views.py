import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import Http404
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from utilities.render import render

from .models import Account
from .forms import AccountForm, UserForm, CreateUserForm


@login_required
@render('accounts/orders.html')
def orders(request):
    from django.apps import apps
    if not apps.is_installed('shoptools.checkout'):
        raise Http404

    from shoptools.checkout.models import Order
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


@render('accounts/details.html')
def details(request):
    if not request.user.is_authenticated:
        if request.is_ajax():
            data = {
                'success': False,
                'errors': 'Please login.',
                'next': reverse('login')
            }
            return HttpResponse(json.dumps(data),
                                content_type='application/json')
        else:
            return redirect('login')

    account = Account.objects.for_user(request.user)

    if request.method == 'POST':
        account_form = AccountForm(request.POST, instance=account)
        user_form = UserForm(request.POST, instance=account.user)
        if account_form.is_valid() and user_form.is_valid():
            account_form.save()
            user_form.save()

            if request.is_ajax():
                data = {
                    'success': True,
                    'errors': [],
                    'next': reverse(details)
                }
                return HttpResponse(json.dumps(data),
                                    content_type='application/json')
            else:
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

    if request.method == 'POST':
        success = False
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
            success = True

        errors = user_form.errors
        errors.update(account_form.errors)

        if request.is_ajax():
            data = {
                'success': success,
                'errors': errors
            }
            return HttpResponse(json.dumps(data),
                                content_type='application/json')
        elif success:
            messages.info(request, 'Your account was created.')
            return redirect(details)
    else:
        account_form = AccountForm(initial=initial)
        user_form = CreateUserForm()

    return {
        'account_form': account_form,
        'user_form': user_form,
    }


@render('accounts/create_user.html')
def create_user(request):
    if request.method == 'POST':
        success = False
        user_form = CreateUserForm(request.POST)
        if user_form.is_valid():
            user = user_form.save()
            auth_user = authenticate(
                username=user.username,
                password=user_form.cleaned_data['password1'])
            login(request, auth_user)
            success = True

        if request.is_ajax():
            data = {
                'success': success,
                'errors': user_form.errors
            }
            return HttpResponse(json.dumps(data),
                                content_type='application/json')
        elif success:
            messages.info(request, 'Your account was created.')
            return redirect(details)
    else:
        user_form = CreateUserForm()

    return {
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
