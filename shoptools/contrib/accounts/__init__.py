def get_account(user):
    from .models import Account
    return Account.objects.for_user(user)


def get_data(request):
    from .util import account_data
    return account_data(request)
