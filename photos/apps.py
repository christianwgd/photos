# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class PhotosAppConfig(AppConfig):
    name = 'photos'
    verbose_name = _('photos')
