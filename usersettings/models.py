# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext as _

from filebrowser.fields import FileBrowseField


class Theme(models.Model):

    class Meta:
        verbose_name = _('Theme')
        verbose_name_plural = _('Themes')
        ordering = ['name']

    def __str__(self):
        return self.name
    
    name = models.CharField(
        verbose_name=_('name'), max_length=50
    )
    cssfile = FileBrowseField(
        _('css file'), max_length=255,
        directory="themes/",
        extensions=[".css"],
        blank=True
    )


class UserSettings(models.Model):

    class Meta:
        verbose_name = _('user settings')
        verbose_name_plural = _('user settings')

    def __str__(self):
        return self.user.username

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    recent = models.DateField(
        _('recent photos since'), help_text=_('None means all'),
        null=True, blank=True
    )
    theme = models.ForeignKey(
        Theme,
        verbose_name=_('Theme'),
        on_delete=models.SET_NULL,
        blank=True, null=True
    )
