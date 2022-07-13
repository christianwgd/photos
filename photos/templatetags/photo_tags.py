# -*- coding:utf-8 -*-
import urllib
from urllib.parse import urlencode

from django import template
from django.db.models import Q

from photos.models import Photo, Gallery, Tag, Import

register = template.Library()


@register.simple_tag
def get_visibles(photos, user):
    """
    get only photos visible for user
    """
    return photos.filter(
        Q(owner=user) |
        Q(shared=user)
    )

@register.filter(name='rotation')
def rotation(value):
    return value * 10 - 20


@register.simple_tag
def can_share(gallery_id, user):
    """
    Test, if user can share gallery,
    user is owner of at least one
    photo in gallery
    :param gallery:
    :return: boolean
    """
    return Photo.objects.filter(gallery__id=gallery_id, owner=user).count() > 0


#remove_query_param request.request.get_full_path item
@register.simple_tag
def remove_query_param(request, item):
    updated = request.GET.copy()
    if item in updated:
        del updated[item]
    return request.path+'?'+updated.urlencode()
