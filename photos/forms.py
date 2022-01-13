# -*- coding: utf-8 -*-
from bootstrap_datepicker_plus.widgets import DateTimePickerInput
from django import forms
from photos import settings
from django_select2.forms import Select2Widget, Select2MultipleWidget

from .models import Photo, Event

lang = getattr(settings, "LANGUAGE_CODE", 'de')


class PhotoForm(forms.ModelForm):

    class Meta:
        model = Photo
        fields = (
            'name', 'event', 'tags', 'owner',
            'timestamp', 'latitude', 'longitude'
        )
        widgets = {
            'event': Select2Widget,
            'owner': Select2Widget,
            'tags': Select2MultipleWidget,
            'timestamp': DateTimePickerInput(
                options={
                    'format': "DD.MM.YYYY HH:mm",
                    'locale': lang,
                },
            )
        }


class EventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = {'name', 'timestamp'}
        widgets = {
            'timestamp': DateTimePickerInput(
                options={
                    'format': "DD.MM.YYYY HH:mm",
                    'locale': lang,
                },
            )
        }
