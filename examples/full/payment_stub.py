from django.shortcuts import redirect


def make_payment(order, request):
    """Fake payment module which set the order's paid status, then redirects
       back. """

    # TODO: simple transaction model, set payment amount equal to
    # order.get_amount() so that it is paid in full.
    order.transaction_succeeded()
    return redirect(order)


def get_checkout_inlines():
    return []
