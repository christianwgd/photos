# -*- coding:utf-8 -*-
from django import template


register = template.Library()


@register.simple_tag
def cut_photos(photos, n):
    """
    cut list to max len
    """
    if n > 0:
        photos = photos[:n]
    return photos


@register.filter(name='rotation')
def rotation(value):
    return value * 10 - 20