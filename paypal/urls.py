try:
    from django.conf.urls import *
except ImportError:
    # pre Django 1.4
    from django.conf.urls.defaults import *
    

urlpatterns = patterns('paypal.views',
    (r'^success/(?P<token>.*)$', 'transaction_success'),
    (r'^failure/(?P<token>.*)$', 'transaction_failure'),
)
