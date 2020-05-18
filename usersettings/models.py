# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
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
        verbose_name=_('name'), max_length=50,
        unique=True
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
    limit = models.PositiveSmallIntegerField(
        default=0, verbose_name=_('Limit unfiltered amount of photos'),
        help_text=_('0 means no limit'),
    )
    recent = models.PositiveSmallIntegerField(
        default=0, verbose_name=_('Recent photos from last days'),
        help_text = _('0 means all'),
    )
    slide_time = models.PositiveSmallIntegerField(
        default=5, verbose_name=_('Slideshow time'),
        help_text=_('Time one slide is shown in seconds')
    )
    theme = models.ForeignKey(
        Theme,
        verbose_name=_('Theme'),
        on_delete=models.SET_NULL,
        blank=True, null=True
    )


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    try:
        user_settings = UserSettings.objects.get(user=instance)
    except UserSettings.DoesNotExist:
        default_theme_name = getattr(settings, "DEFAULT_THEME", None)
        if default_theme_name is not None:
            default_theme = Theme.objects.get(name=default_theme_name)
        else:
            default_theme = None
        UserSettings.objects.create(
            user = instance,
            theme = default_theme
        )
