def make_payment(content_object, request=None, transaction_opts={},
                 get_return_url=None):
    from .transactions import make_payment
    return make_payment(content_object, request, transaction_opts,
                        get_return_url)


def get_transaction(secret):
    from .transactions import get_transaction
    return get_transaction(secret)


def get_checkout_inlines():
    from .admin import TransactionInlineAdmin
    return [TransactionInlineAdmin]
