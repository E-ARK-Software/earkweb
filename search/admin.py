from django.contrib import admin
from search.models import Package
from search.models import DIPackage

admin.site.register(Package)
admin.site.register(DIPackage)
