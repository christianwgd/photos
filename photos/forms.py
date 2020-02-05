# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django import forms
from tempus_dominus.widgets import DateTimePicker

from .models import Photo


class PhotoForm(forms.ModelForm):

    class Meta:
        model = Photo
        fields = (
            'name', 'event', 'tags', 'owner',
            'timestamp', 'latitude', 'longitude'
        )
        widgets = {
            'timestamp': DateTimePicker(
                    options={
                        'useCurrent': True,
                        'collapse': False,
                    },
                    attrs={
                        'append': 'fa fa-calendar',
                        'icon_toggle': True,
                    }
                )
        }
