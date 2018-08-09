from django.conf.urls import url

from . import views

urlpatterns = (
    url(r'^execute/(?P<token>.*)$', views.execute_transaction, {},
        'paypal_execute_transaction'),
    url(r'^result/(?P<token>.*)$', views.transaction_result, {},
        'paypal_transaction_result'),
)
