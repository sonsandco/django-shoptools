from django.shortcuts import redirect


def make_payment(order, request):
    """Fake payment module which set the order's paid status, then redirects
       back. """

    order.transaction_succeeded(0)
    return redirect(order)
