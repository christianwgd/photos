# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

from django.contrib import admin
from django.contrib.admin import AdminSite

from .models import Photo


class MyAdminSite(AdminSite):
    site_title = _('Photos')
    site_header = _('Photos')
    index_title = _('Management')


class PhotoAdmin(admin.ModelAdmin):
    search_fields = ['name', 'imagefile']


admin.site.register(Photo, PhotoAdmin)
