from pprint import pformat

from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect

# from decorators import dps_result_view
from models import Transaction
import settings as paypal_settings
from transactions import finish_payment


if paypal_settings.TEMPLATE_ENGINE in ['jinja', 'jinja2']:
    from coffin.shortcuts import render_to_response
else:
    from django.shortcuts import render_to_response


# @dps_result_view
def transaction_success(request, token):
    transaction = get_object_or_404(Transaction.objects.filter(status__in=[Transaction.PROCESSING,
                                                                          Transaction.SUCCESSFUL]),
                                    secret=token)
    
    result = finish_payment(transaction, request)
    
    transaction.status = Transaction.SUCCESSFUL
    transaction.result = pformat(result, width=1)
    transaction.save()

    content_object = transaction.content_object
    
    # callback, if it exists. It may optionally return a url for redirection
    success_url = getattr(content_object,
                          "transaction_succeeded",
                          lambda *args: None)(transaction, True)
    
    if success_url:
        # assumed to be a valid url
        return HttpResponseRedirect(success_url)
    else:
        return render_to_response("dps/transaction_success.html", RequestContext(request, {
                    "transaction": transaction}))


# @dps_result_view
def transaction_failure(request, token):
    transaction = get_object_or_404(Transaction.objects.filter(status__in=[Transaction.PROCESSING,
                                                                           Transaction.FAILED]),
                                    secret=token)
    transaction.status = Transaction.FAILED
    # transaction.result = pformat(result, width=1)
    transaction.save()
    
    content_object = transaction.content_object
    
    # callback, if it exists. It may optionally return a url for redirection
    failure_url = getattr(content_object,
                          "transaction_failed",
                          lambda *args: None)(transaction, True)
    
    if failure_url:
        # assumed to be a valid url
        return HttpResponseRedirect(failure_url)
    else:
        return render_to_response("dps/transaction_failure.html", RequestContext(request, {
                "transaction": transaction}))

