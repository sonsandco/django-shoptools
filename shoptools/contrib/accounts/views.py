import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.http import Http404, HttpResponseRedirect
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from shoptools import settings as shoptools_settings

from .models import Account
from .forms import \
    EmailAuthenticationForm, AccountForm, UserForm, CreateUserForm
from .signals import \
    create_pre_save, create_post_save, update_pre_save, update_post_save


def login(request):
    ctx = {}

    # Some apps (eg. shoptools.contrib.favourites) require the user to be
    # authenticated to undertake certain actions. Typically those apps will
    # redirect to the login page if an action is attempted whule not logged in.
    # To avoid the user having to redo the action after login, we allow apps to
    # additional POST data in session[LOGIN_ADDITIONAL_POST_DATA_KEY], and if
    # present we process that data after login.
    # The POST data is always retrieved from the session by this view; if it
    # was a GET request the POST data is passed to the template so it will
    # be submitted together with the login details. This somewhat convoluted
    # approach is to ensure that if the user changes their mind (ie. navigates
    # away instead of logging in) the action is not undertaken if they then log
    # in at some later point.
    additional_post_data = request.session.pop(
        shoptools_settings.LOGIN_ADDITIONAL_POST_DATA_KEY, {})
    if additional_post_data:
        request.session.modified = True

    if request.method == 'POST':
        success = False
        next_url = request.POST.get('next', '')

        auth_form = EmailAuthenticationForm(data=request.POST)

        if not additional_post_data:
            # Get additional data from POST
            # request.POST.get('additional_data_app')
            # request.POST.get('additional_data_action')
            pass

        if auth_form.is_valid():
            user = auth_form.get_user()
            auth_login(request, user)
            success = True

            if additional_post_data:
                # process it now
                pass

            if request.is_ajax():
                data = {
                    'success': success,
                    'errors': auth_form.errors,
                    'redirect_to': next_url
                }
                return HttpResponse(json.dumps(data),
                                    content_type='application/json')
            else:
                return HttpResponseRedirect(
                    next_url or request.META.get('HTTP_REFERER', '/'))
    else:
        next_url = request.GET.get('next', '')
        auth_form = EmailAuthenticationForm()

    ctx.update({
        'form': auth_form,
        'next': next_url,
        'additional_post_data': additional_post_data
    })

    return render(request, 'registration/login.html', ctx)


@login_required
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

    ctx = {
        'orders': orders,
        'current': current,
        'completed': completed,
    }

    return render(request, 'accounts/orders.html', ctx)


def details(request):
    if not request.user.is_authenticated:
        if request.is_ajax():
            data = {
                'success': False,
                'errors': ['Please login.'],
                'redirect_to': reverse('login'),
                'next': reverse(details)
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
            update_pre_save.send(sender=Account, request=request)
            account_form.save()
            user_form.save()
            update_post_save.send(sender=Account, request=request)

            if request.is_ajax():
                data = {
                    'success': True,
                    'errors': [],
                    'redirect_to': reverse(details)
                }
                return HttpResponse(json.dumps(data),
                                    content_type='application/json')
            else:
                messages.info(request, 'Your details were saved')
                return redirect(details)
    else:
        account_form = AccountForm(instance=account)
        user_form = UserForm(instance=account.user)

    ctx = {
        'account_form': account_form,
        'user_form': user_form,
    }

    return render(request, 'accounts/details.html', ctx)


def create(request):
    initial = {}

    if request.method == 'POST':
        success = False
        account_form = AccountForm(request.POST, initial=initial)
        user_form = CreateUserForm(request.POST)
        if account_form.is_valid() and user_form.is_valid():
            account = account_form.save(commit=False)
            account.user = user_form.save()
            create_pre_save.send(sender=Account, request=request)
            account.save()
            auth_user = authenticate(
                username=account.user.username,
                password=user_form.cleaned_data['password1'])
            auth_login(request, auth_user)
            success = True
            create_post_save.send(sender=Account, request=request)

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

    ctx = {
        'account_form': account_form,
        'user_form': user_form,
    }

    return render(request, 'accounts/create.html', ctx)


def create_user(request):
    if request.method == 'POST':
        success = False
        user_form = CreateUserForm(request.POST)
        if user_form.is_valid():
            user = user_form.save()
            auth_user = authenticate(
                username=user.username,
                password=user_form.cleaned_data['password1'])
            auth_login(request, auth_user)
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

    ctx = {
        'user_form': user_form,
    }

    return render(request, 'accounts/create_user.html', ctx)
