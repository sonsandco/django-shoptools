from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^checkout/', include('shoptools.checkout.urls')),
    url(r'^cart/', include('shoptools.cart.urls')),
    url(r'^', include('shoptools.contrib.catalogue.urls')),
    url(r'^accounts/', include('shoptools.contrib.accounts.urls')),
    url(r'^payment/', include('shoptools.contrib.paypal.urls')),
    url(r'^regions/', include('shoptools.contrib.regions.urls')),
    url(r'^shipping/', include('shoptools.contrib.shipping.urls')),

]
