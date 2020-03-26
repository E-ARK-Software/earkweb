# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from earkweb.models import RepoUser


# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class RepoUserInline(admin.StackedInline):
    model = RepoUser
    can_delete = False
    verbose_name_plural = 'repouser'


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (RepoUserInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
