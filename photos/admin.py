# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import AdminSite
from django.contrib import admin

from .models import Photo, Event, Tag



AdminSite.site_title = _('Photos')
AdminSite.site_header = _('Photos')
AdminSite.index_title = _('Photos ADMINISTRATION')

class PhotoAdmin(admin.ModelAdmin):
    search_fields = ['name', 'address',]
    list_filter = ['event', 'tags']


class EventAdmin(admin.ModelAdmin):
    search_fields = ['name',]


class TagAdmin(admin.ModelAdmin):
    search_fields = ['name',]



admin.site.register(Photo, PhotoAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Tag, TagAdmin)