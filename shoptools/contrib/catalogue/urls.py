from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, {}, 'catalogue_index'),
    url(r'^product/(\d+)$', views.detail, {}, 'catalogue_detail'),
]
