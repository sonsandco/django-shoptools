Accounts reference
===

`SHOPTOOLS_ACCOUNTS_MODULE` must provide function to get account instance for a user

```
get_user_account(user):
    return Account()
```

and function to get current session data from a request

```
def get_data(request):
    return {}
```
