from django.conf.urls import patterns, url


urlpatterns = patterns('checkout.views',
    url(r'^cart$', 'cart'),
    url(r'^$', 'checkout'),
    url(r'^(\w+)$', 'checkout'),
    url(r'^(\w+)/success$', 'success'),
)
