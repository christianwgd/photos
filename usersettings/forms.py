# -*- coding: utf-8 -*-
from django.forms import ModelForm

from .models import UserSettings


class UserSettingsForm(ModelForm):
    class Meta:
        model = UserSettings
        fields = ['limit', 'recent', 'slide_time', 'theme']
