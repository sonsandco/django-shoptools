from django.conf.urls import url

from . import views

urlpatterns = (
    url(r'^cart$', views.cart, {}, 'checkout_cart'),
    url(r'^checkout$', views.checkout, {}, 'checkout_checkout'),
)
