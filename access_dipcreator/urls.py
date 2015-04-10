from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import RedirectView
import os

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'access_dipcreator.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    
    url(r'^$', RedirectView.as_view(url='search/')),
    url(r'^search/', include('search.urls', namespace="search")),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django_cas.views.login'), 
    url(r'^accounts/logout/$', 'django_cas.views.logout'),
)

# Development server starts at http://127.0.0.1:8888/ so this rule is adds
# the URL prefix path
if "Development/" in os.path.dirname(os.path.dirname(os.path.abspath(__file__))):
    urlpatterns = patterns('',
        url(r'^$', RedirectView.as_view(url='access_dipcreator/')),
        url(r'^access_dipcreator/', include(urlpatterns)),
    )
