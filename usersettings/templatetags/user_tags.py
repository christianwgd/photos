# -*- coding:utf-8 -*-
from django import template
from django.utils.html import mark_safe
from usersettings.models import UserSettings


register = template.Library()


@register.simple_tag
def user_theme(user):
    """
    get user specific bootstrap theme
    """

    try:
        if user.is_authenticated:
            user_settings = UserSettings.objects.get(user=user)
            if user_settings.theme is not None:
                theme_url = user_settings.theme.cssfile.url
                theme_tag = '<link rel="stylesheet" href="{url}">'.format(
                    url = theme_url
                )
                return mark_safe(theme_tag)
    except UserSettings.DoesNotExist:
        pass
    return ''