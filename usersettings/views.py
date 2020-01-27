# -*- coding: utf-8 -*-
from django.contrib import messages
from django.shortcuts import HttpResponseRedirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required

from .forms import UserSettingsForm
from .models import UserSettings


@login_required(login_url='/accounts/login/')
def settings(request):

    if 'cancel' in request.POST:
        messages.info(request, _('edit cancelled'))
        return HttpResponseRedirect(reverse('photolist'))

    try:
        user_settings = UserSettings.objects.get(user=request.user)
    except UserSettings.DoesNotExist:
        user_settings = UserSettings(user=request.user)

    if request.method == 'POST':
        settings_form = UserSettingsForm(
            request.POST, instance=user_settings)

        if settings_form.is_valid():

            try:
                if settings_form.has_changed():
                    settings_form.save()
                messages.success(
                    request,
                    _('settings saved for user {user}').format(
                        user=request.user
                    )
                )
                return HttpResponseRedirect(reverse('photolist'))
            except Exception as e:
                messages.error(
                    request, _('error saving settings: {}'.format(e)))
    else:  # GET
        settings_form = UserSettingsForm(instance=user_settings)

    return render(request, 'usersettings/user_settings.html', {
        'settingsform': settings_form,
    })
