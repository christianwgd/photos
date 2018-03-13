# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class UserSettingsConfig(AppConfig):
    name = 'usersettings'
    verbose_name = _('User settings')
