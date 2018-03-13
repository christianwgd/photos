# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


class UserSettings(models.Model):

    def __str__(self):
        return self.iban

    class Meta:
        verbose_name = _('user settings')
        verbose_name_plural = _('user settings')

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    recent = models.PositiveIntegerField(_('number of recent photos'))
