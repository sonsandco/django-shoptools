import warnings

from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.shortcuts import render_to_response
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from .models import Transaction
from .transactions import execute_payment


def get_transaction_url(transaction):
    status = transaction.status
    obj = transaction.content_object

    if status == Transaction.SUCCESSFUL and \
            hasattr(obj, 'transaction_success_url'):
        return obj.transaction_success_url(transaction)

    elif status == Transaction.FAILED and \
            hasattr(obj, 'transaction_failure_url'):
        return obj.transaction_failure_url(transaction)

    return reverse('paypal_transaction_result', args=(transaction.secret, ))


def execute_transaction(request, token):
    '''
    Execute a created Paypal transaction, redirecting to the appropriate
    'success' or 'failure' page. This view is idempotent; repeated requests
    should just redirect to the result page without hitting Paypal.
    '''
    transaction = get_object_or_404(Transaction, secret=token)

    # Redirecting if the transaction is already processed
    if transaction.status in (Transaction.SUCCESSFUL, Transaction.FAILED):
        return redirect(get_transaction_url(transaction))

    # Don't process transactions that aren't at the correct stage
    if transaction.status != Transaction.CREATED:
        raise Http404

    success = execute_payment(transaction, request)

    # update transaction status according to success
    status_updated = transaction.complete_transaction(success)
    if not status_updated:
        # shouldn't ever get here, but in the event Paypal sends two responses
        # in very quick succession there's a tiny race condition which
        # means it might, so raise the 404 that would normally happen above.
        raise Http404

    redirect_url = None

    # call the callback if it exists
    callback_name = 'transaction_succeeded' if success else \
                    'transaction_failed'
    callback = getattr(transaction.content_object, callback_name, None)

    if callback:
        redirect_url = callback(transaction)

        if redirect_url:
            warnings.warn(
                'Returning a url from the transaction_succeeded or '
                'transaction_failed methods is deprecated, use '
                'transaction_success_url or transaction_failure_url instead',
                DeprecationWarning)

    if not redirect_url:
        redirect_url = get_transaction_url(transaction)

    return redirect(redirect_url)


def transaction_result(request, token):
    transaction = get_object_or_404(Transaction, secret=token,
                                    status__in=[Transaction.SUCCESSFUL,
                                                Transaction.FAILED])
    return render_to_response('paypal/transaction_result.html', {
        'request': request,
        'transaction': transaction,
        'success': (transaction.status == Transaction.SUCCESSFUL),
    })
