def get_account(user):
    from .models import Account
    return Account.objects.for_user(user)
