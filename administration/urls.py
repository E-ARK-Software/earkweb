from django.urls import re_path, path
import administration.views

app_name = 'administration'

urlpatterns = [
    re_path(r'^$', administration.views.backendadmin, name='default'),
    re_path(r'^dashboard$', administration.views.dashboard, name='dashboard'),
    re_path(r'^backendadmin', administration.views.backendadmin, name='backendadmin'),

]
