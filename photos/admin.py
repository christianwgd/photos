# -*- coding: utf-8 -*-

from django.utils.translation import gettext_lazy as _
from django.contrib.admin import AdminSite
from django.contrib import admin

from .models import Photo, Gallery, Tag, Import

AdminSite.site_title = _('Photos')
AdminSite.site_header = _('Photos')
AdminSite.index_title = _('Photos administration')


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    search_fields = ['name', 'address',]
    list_filter = ['gallery', 'tags', 'owner', 'upload']
    autocomplete_fields = ['shared', 'tags']


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    search_fields = ['name',]
    autocomplete_fields = ['visible_for']


@admin.register(Import)
class ImportAdmin(admin.ModelAdmin):
    search_fields = ['name',]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ['name',]
