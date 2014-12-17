import urllib, urllib2
from xml.etree import cElementTree as ElementTree
from django.conf import settings
from django.http import HttpResponseRedirect
from dps.models import Transaction


def _get_setting(name):
    return getattr(settings, name,
                   Exception("Please specify %s in settings." % name))



# def _get_response(url, xml_body):
#     """Takes and returns an ElementTree xml document."""
#     req = urllib2.Request(url, ElementTree.tostring(xml_body, encoding='utf-8'))
#     response = urllib2.urlopen(req)
#     return ElementTree.fromstring(response.read())
# 
# 
# def _params_to_xml_doc(params, root="GenerateRequest"):
#     """This function works in this simpler form because we never have
#     to send nested structures to DPS; all sent structures are just a
#     list of key=value inside a single root tag."""
#     root_tag = ElementTree.Element(root)
#     for (key, value) in params.items():
#         # No params will be modified beyond this point, so if we still
#         # have an Exception placeholder it's time to throw it.
#         if isinstance(value, Exception):
#             raise value
#         elem = ElementTree.Element(key)
#         elem.text = unicode(value)
#         root_tag.append(elem)
# 
#     return root_tag
# 
# 
# def begin_interactive(params):
#     """Takes a params dictionary, returns the redirect to the DPS page
#     to complete payment."""
#     assert "UrlFail" in params
#     assert "UrlSuccess" in params
#     assert "MerchantReference" in params
#     assert "AmountInput" in params
# 
#     merged_params = {}
#     merged_params.update(PXPAY_DEFAULTS)
#     merged_params.update(params)
# 
#     response = _get_response(PXPAY_URL,
#                              _params_to_xml_doc(merged_params,
#                                                 root="GenerateRequest"))
# 
#     return HttpResponseRedirect(response.find("URI").text)
# 

# def get_interactive_result(result_key):
#     """Unfortunately PxPay and PxPost have different XML reprs for
#     transaction results, so we need a specific function for each.
# 
#     This function returns a dictionary of all the available params."""
#     params = {
#         "PxPayUserId": _get_setting("PXPAY_USERID"),
#         "PxPayKey": _get_setting("PXPAY_KEY"),
#         "Response": result_key}
#     result = _get_response(PXPAY_URL,
#                            _params_to_xml_doc(params, root="ProcessResponse"))
# 
#     output = {}
#     for key in ["Success", "TxnType", "CurrencyInput", "MerchantReference",
#                 "TxnData1", "TxnData2", "TxnData3", "AuthCode", "CardName",
#                 "CardHolderName", "CardNumber", "DateExpiry", "ClientInfo",
#                 "TxnId", "EmailAddress", "DpsTxnRef", "BillingId",
#                 "DpsBillingId", "TxnMac", "ResponseText", "CardNumber2"]:
#         output[key] = result.find(key).text
# 
#     output["valid"] = result.get("valid")
#     
#     return output

def make_payment(content_object, request=None, transaction_opts={}):
    """"""
    
    trans = Transaction(content_object=content_object)
    trans.status = Transaction.PROCESSING
    trans.save()

    # Basic params, needed in all cases.
    params = {amount_name: u"%.2f" % trans.amount,
              "MerchantReference": trans.merchant_reference}

    # set up params for an interactive payment
    url_root = u"http://%s" % request.META['HTTP_HOST']
    params.update({"UrlFail": url_root + trans.get_failure_url(),
                   "UrlSuccess": url_root + trans.get_success_url()})
    
    params.update(transaction_opts)

    return begin_interactive(params)
    
