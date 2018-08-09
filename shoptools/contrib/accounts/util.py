from .models import Account


def get_account(user):
    return Account.objects.for_user(user)


def account_context(request):
    data = {}
    user = request.user
    if request.user.is_authenticated:
        data.update({
            'user': request.user
        })
        account = get_account(user)
        data.update({
            'account': account
        })
    return data


def account_data(request):
    data = account_context(request)

    if 'user' in data:
        data['user'] = {
            'first_name': data['user'].first_name,
            'last_name': data['user'].last_name,
            'email': data['user'].email,
        }

    if 'account' in data:
        data['account'] = data['account'].as_dict()

    return data
