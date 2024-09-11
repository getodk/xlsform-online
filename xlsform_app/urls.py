from django.conf.urls import url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^downloads/(?P<path>.*)$', views.serve_file),
    url(r'^api/xlsform$', views.api_xlsform),
]

urlpatterns += staticfiles_urlpatterns()
