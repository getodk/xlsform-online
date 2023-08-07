from django.conf.urls import url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^downloads/(?P<path>.*)$', views.serve_file),
]

urlpatterns += staticfiles_urlpatterns()
