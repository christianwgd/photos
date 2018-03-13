# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import UserSettings


class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'recent', ]


admin.site.register(UserSettings, UserSettingsAdmin)
