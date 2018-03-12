# -*- coding: utf-8 -*-

from django.utils.translation import ugettext as _
from django.apps import AppConfig


class PhotosConfig(AppConfig):
    name = 'photos'
    verbose_name = _('photos')
    label = _('photos')
