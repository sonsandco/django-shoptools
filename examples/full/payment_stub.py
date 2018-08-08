from django.shortcuts import redirect


class Transaction(object):
    def __init__(self, amount):
        self.amount = amount


def make_payment(order, request):
    """
    Fake payment module which simply passes a transaction with amount set to
    the amount owing to transaction_succeeded, then redirects to the
    order's absolute url.
    """

    transaction = Transaction(amount=order.get_amount())
    order.transaction_succeeded(transaction)
    return redirect(order)


def get_checkout_inlines():
    return []
