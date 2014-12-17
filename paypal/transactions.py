# import json

import urllib, urllib2, base64, subprocess, os
from decimal import Decimal
import json

# from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.sites.models import Site
# from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from models import Transaction


if settings.PAYPAL_DEBUG:
  PAYPAL_API = 'https://api.sandbox.paypal.com'
  PAYPAL_CLIENT_ID = settings.PAYPAL_SANDBOX_CLIENT_ID
  PAYPAL_SECRET = settings.PAYPAL_SANDBOX_SECRET
else:
  PAYPAL_API = 'https://api.paypal.com'
  PAYPAL_CLIENT_ID = settings.PAYPAL_CLIENT_ID
  PAYPAL_SECRET = settings.PAYPAL_SECRET


def build_url(request, path):
  return ''.join((
    'https://' if request.is_secure() else 'http://',
    Site.objects.get_current().domain,
    path,
  ))


def basic_authorization(user, password):
  s = user + ":" + password
  return "Basic " + s.encode("base64").rstrip()


def get_paypal_token():
  '''Gets a paypal auth token for subsequent api calls as per 
     https://developer.paypal.com/docs/integration/direct/paypal-oauth2/
  '''
  
  url = PAYPAL_API + '/v1/oauth2/token'
  params = { "grant_type": 'client_credentials'}
  credentials = (PAYPAL_CLIENT_ID, PAYPAL_SECRET)
  # If someone can get this to work with a less horrific technique, please
  # go ahead. urllib2 and subprocess don't work (I get an unhelpful paypal
  # error and can't work out why) and requests is not available on py2.5
  curl_command = 'curl %s -H "Accept: application/json" ' \
                         '-H "Accept-Language: en_US" ' \
                         '-u "%s:%s" ' \
                         '-d "grant_type=client_credentials" -s' % \
                         (url, credentials[0], credentials[1])
  curl_output = os.popen(curl_command)
  result = curl_output.read()
  data = json.loads(result)
  
  return data['access_token']


def get_link(data, link_type):
  links = dict((d['rel'], d) for d in data['links'])
  return links[link_type]['href']


def make_payment(content_object, request, transaction_opts={}):
  """"""

  trans = Transaction(content_object=content_object)
  trans.status = Transaction.PROCESSING
  trans.save()
  
  total = content_object.get_amount()
  shipping = content_object.shipping_cost()
  subtotal = (total - shipping)
  
  post_data = {
    'intent':'sale',
    'redirect_urls':{
        'return_url': build_url(request, trans.get_success_url()),
        'cancel_url': build_url(request, trans.get_failure_url()),
    },
    'payer':{
        'payment_method': 'paypal',
    },
    'transactions': [{
      'amount': {
        'total': "%.2f" % total,
        'currency': content_object.currency,
        'details': {
          'subtotal': "%.2f" % subtotal,
          'shipping': "%.2f" % shipping,
        }
      },
      'description': unicode(content_object).encode('ascii', 'ignore'),
      'item_list': {'items': []},
    }]
  }
  
  if hasattr(content_object, 'get_lines'):
    for line in content_object.get_lines():
      post_data['transactions'][0]['item_list']['items'].append({
        'name': '%s x %s' % (line[1], line[0]),
        'quantity': 1,
        'price': "%.2f" % line[2],
        'currency': content_object.currency,
      })
  else:
    post_data['transactions'][0]['item_list']['items'].append({
      'quantity': 1,
      'name': unicode(content_object).encode('ascii', 'ignore'),
      'price': "%.2f" % subtotal,
      'currency': content_object.currency,
    })
  
  url = PAYPAL_API + '/v1/payments/payment'
  token = get_paypal_token()
  
  # see https://developer.paypal.com/docs/integration/web/accept-paypal-payment/#specify-payment-information-to-create-a-payment
  
  opener = urllib2.build_opener(BetterHTTPErrorProcessor)
  urllib2.install_opener(opener)
  
  encoded_data = json.dumps(post_data)

  request = urllib2.Request(url, encoded_data,
                            headers={"Authorization": 'Bearer ' + token,
                                     "Content-Type": 'application/json'})
  try:
    request = urllib2.Request(url, encoded_data,
                              headers={"Authorization": 'Bearer ' + token,
                                       "Content-Type": 'application/json'})
    result = urllib2.urlopen(request).read()
  except urllib2.HTTPError, e:
    raise Exception(e.read())
  else:
    result_data = json.loads(result)
    
    trans.result = result
    trans.save()
    return HttpResponseRedirect(get_link(result_data, 'approval_url'))


def finish_payment(trans, request):
  result_data = json.loads(trans.result)
  url = get_link(result_data, 'execute')
  payer_id = request.GET['PayerID']
  token = get_paypal_token()
  encoded_data = json.dumps({'payer_id': payer_id})
  request = urllib2.Request(url, encoded_data,
                            headers={"Authorization": 'Bearer ' + token,
                                     "Content-Type": 'application/json'})
  try:
    result = urllib2.urlopen(request).read()
  except urllib2.HTTPError, e:
    raise Exception(e.read())

  # trans.result = result
  result_data = json.loads(result)

  # TODO: save actual data here
  
  return result_data
  


# def make_payment(order, request):
#   if param:
#     payment_attempt = get_object_or_404(content_object.paymentattempt_set, 
#                                         hash=param)
#     
#     result_data = json.loads(payment_attempt.result)
#     url = get_link(result_data, 'execute')
#     payer_id = request.GET['PayerID']
#     token = get_paypal_token()
#     encoded_data = json.dumps({'payer_id': payer_id})
#     request = urllib2.Request(url, encoded_data,
#                               headers={"Authorization": 'Bearer ' + token,
#                                        "Content-Type": 'application/json'})
#     result = urllib2.urlopen(request).read()
#     payment_attempt.result = result
#     result_data = json.loads(result)
#     
#     amount = sum([Decimal(t['amount']['total']) for t in 
#                   result_data['transactions']])
#     payment_attempt.amount = amount
#     
#     success = result_data['state'] in ('pending', 'approved')
#     payment_attempt.success = success
#     payment_attempt.transaction_ref = result_data['id']
#     payment_attempt.save()
#     
#     if success:
#       payer = result_data['payer']['payer_info']
#       content_object.name = payer['first_name'] + ' ' + payer['last_name']
#       content_object.email = payer['email']
#       content_object.street_address = payer['shipping_address']['line1']
#       content_object.suburb = payer['shipping_address']['line2']
#       content_object.city = payer['shipping_address']['city']
#       content_object.post_code = payer['shipping_address']['postal_code']
#       content_object.country = payer['shipping_address']['country_code']
#       # content_object.phone = 
#       
#       content_object.payment_successful = True
#       content_object.save()
#       return HttpResponseRedirect(content_object.get_absolute_url())
#   
#   payment_attempt = content_object.paymentattempt_set.create()
#   
#   return_url = build_url(request, 'cart.views.payment', 
#                          (content_object.hash, payment_attempt.hash, ))
#   # cancel URL takes user back to previous step
#   cancel_url = build_url(request, 'cart.views.delivery')
#   
#   post_data = {
#     'intent':'sale',
#     'redirect_urls':{
#         'return_url': return_url,
#         'cancel_url': cancel_url,
#     },
#     'payer':{
#         'payment_method': 'paypal',
#     },
#     'transactions': [{
#       'amount': {
#         'total': "%.2f" % content_object.total(),
#         'currency': get_currency(order),
#         'details': {
#           'subtotal': "%.2f" % (content_object.total() - content_object.shipping_cost),
#           'shipping': "%.2f" % content_object.shipping_cost,
#         }
#       },
#       'description': unicode(order).encode('ascii', 'ignore'),
#       'item_list': { 
#         'items': [{
#                     'quantity': str(line.quantity),
#                     'name': unicode(line).encode('ascii', 'ignore'),
#                     'price': "%.2f" % line.price,
#                     'currency': get_currency(order),
#                   }
#                   for line in content_object.orderline_set.all()]
#       }
#     }]
#   }
#   print post_data
#   url = PAYPAL_API + '/v1/payments/payment'
#   
#   token = get_paypal_token()
#   
#   
#   # see https://developer.paypal.com/docs/integration/web/accept-paypal-payment/#specify-payment-information-to-create-a-payment
#   
#   opener = urllib2.build_opener(BetterHTTPErrorProcessor)
#   urllib2.install_opener(opener)
#   
#   encoded_data = json.dumps(post_data)
#   request = urllib2.Request(url, encoded_data,
#                             headers={"Authorization": 'Bearer ' + token,
#                                      "Content-Type": 'application/json'})
#   result = urllib2.urlopen(request).read()
#   result_data = json.loads(result)
#   
#   payment_attempt.result = result
#   payment_attempt.save()
#   return HttpResponseRedirect(get_link(result_data, 'approval_url'))


class BetterHTTPErrorProcessor(urllib2.BaseHandler):
  # a substitute/supplement to urllib2.HTTPErrorProcessor
  # that doesn't raise exceptions on status codes 201,204,206
  def http_error_201(self, request, response, code, msg, hdrs):
      return response
  def http_error_204(self, request, response, code, msg, hdrs):
      return response
  def http_error_206(self, request, response, code, msg, hdrs):
      return response