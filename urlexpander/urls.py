from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.url_list, name='url_list'),
    url(r'^urlexpander/(?P<pk>[0-9]+)/$', views.url_detail, name='url_detail'),
    url(r'^urlexpander/new/$', views.url_add, name='url_add'),
    url(r'^urlexpander/remove/(?P<pk>[0-9]+)/$', views.url_remove, name='url_remove'),
    url(r'^api/$', views.api_url_list, name='url-list'),
    url(r'^api/(?P<pk>[0-9]+)/$', views.api_url_detail, name='url-detail'),
    url(r'^refresh/(?P<pk>[0-9]+)/$', views.refresh_screenshot, name='refresh-screenshot')
]
