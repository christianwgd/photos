# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import AdminSite
from django.contrib import admin

from .models import Photo, Event, Tag, Import

AdminSite.site_title = _('Photos')
AdminSite.site_header = _('Photos')
AdminSite.index_title = _('Photos administration')

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    search_fields = ['name', 'address',]
    list_filter = ['event', 'tags', 'owner', 'upload']
    autocomplete_fields = ['shared', 'tags']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    search_fields = ['name',]


@admin.register(Import)
class ImportAdmin(admin.ModelAdmin):
    search_fields = ['name',]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ['name',]
