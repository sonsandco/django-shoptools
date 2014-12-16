from django.conf.urls import url, patterns

urlpatterns = patterns('cart.views',
    url(r'^$', 'get_cart'),
    url(r'^update/$', 'update_cart'),
    url(r'^add/$', 'add'),
    url(r'^remove/$', 'remove'),
    url(r'^clear/$', 'clear'),
)
