from django.conf.urls import url

import administration.views

app_name = 'administration'

urlpatterns = [
    url(r'^$', administration.views.backendadmin, name='default'),
    url(r'^dashboard$', administration.views.dashboard, name='dashboard'),
    url(r'^backendadmin', administration.views.backendadmin, name='backendadmin'),

]
