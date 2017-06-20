from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^checkout/', include('shoptools.checkout.urls')),
    url(r'^cart/', include('shoptools.cart.urls')),

    url(r'^', include('shoptools.contrib.catalogue.urls')),
]
