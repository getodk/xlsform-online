from django.urls import re_path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . import views

urlpatterns = [
    re_path(r'^$', views.index),
    re_path(r'^downloads/(?P<path>.*)$', views.serve_file),
    re_path(r'^api/xlsform$', views.api_xlsform),
]

urlpatterns += staticfiles_urlpatterns()
