#!/usr/bin/env python
# -*- coding:utf-8 -*-

from overtime.models import ApplicationState, Application, UserProfile
from django.contrib import admin

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'chinese_name', 'english_name')

admin.site.register(ApplicationState)
admin.site.register(Application)
admin.site.register(UserProfile, UserProfileAdmin)
