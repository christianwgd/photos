# -*- coding:utf-8 -*-
from datetime import timedelta, date

from django import template
from django.utils.html import mark_safe

from photos import settings
from usersettings.models import UserSettings
from django.utils.formats import date_format


register = template.Library()


@register.simple_tag
def user_theme(user):
    """
    get user specific bootstrap theme
    """

    theme_url = getattr(settings, 'DEFAULT_THEME', '/static/css/bootstrap.min.css')
    if user.is_authenticated:
        try:
            user_settings = UserSettings.objects.get(user=user)
            if user_settings.theme is not None:
                theme_url = user_settings.theme.cssfile.url
        except UserSettings.DoesNotExist:
            pass
    theme_tag = '<link rel="stylesheet" href="{url}">'.format(
        url=theme_url
    )
    return mark_safe(theme_tag)


@register.simple_tag
def recent_date_param(user):
    """
    get user specific recent date parameter
    """

    try:
        if user.is_authenticated:
            user_settings = UserSettings.objects.get(user=user)
            if user_settings.recent is not None and user_settings.recent > 0:
                td = date.today() - timedelta(days=user_settings.recent)
                recent_param = '?timestamp_after={date}'.format(
                    date = date_format(td, "SHORT_DATE_FORMAT")
                )
                return mark_safe(recent_param)
    except UserSettings.DoesNotExist:
        pass
    return ''