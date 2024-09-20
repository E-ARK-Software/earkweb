from django.urls import re_path
import oai_pmh.views

app_name = 'oai_pmh'

urlpatterns = [
    re_path(r'^$', oai_pmh.views.oai_pmh, name='oai_pmh'),
]
