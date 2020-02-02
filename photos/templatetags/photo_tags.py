# -*- coding:utf-8 -*-
from django import template
from django.db.models import Q

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

