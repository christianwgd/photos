# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

from django.contrib import admin

from .models import Photo, Event, Tag


class PhotoAdmin(admin.ModelAdmin):
    search_fields = ['name', 'address',]


class EventAdmin(admin.ModelAdmin):
    search_fields = ['name',]


class TagAdmin(admin.ModelAdmin):
    search_fields = ['name',]


admin.site.register(Photo, PhotoAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Tag, TagAdmin)