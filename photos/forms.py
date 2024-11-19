# -*- coding: utf-8 -*-
from bootstrap_datepicker_plus.widgets import DateTimePickerInput
from django import forms
from photos import settings
from django_select2.forms import Select2Widget, Select2MultipleWidget

from .models import Photo, Gallery

lang = getattr(settings, "LANGUAGE_CODE", 'de')


class PhotoForm(forms.ModelForm):

    class Meta:
        model = Photo
        fields = (
            'name', 'gallery', 'tags', 'owner',
            'timestamp', 'latitude', 'longitude'
        )
        widgets = {
            'gallery': Select2Widget(attrs={'data-theme': 'bootstrap'}),
            'owner': Select2Widget(attrs={'data-theme': 'bootstrap'}),
            'tags': Select2MultipleWidget(attrs={'data-theme': 'bootstrap'}),
            'timestamp': DateTimePickerInput(
                options={
                    'format': "DD.MM.YYYY HH:mm",
                    'locale': lang,
                },
            )
        }


class GalleryForm(forms.ModelForm):

    class Meta:
        model = Gallery
        fields = {'name', 'image'}
        widgets = {
            'timestamp': DateTimePickerInput(
                options={
                    'format': "DD.MM.YYYY HH:mm",
                    'locale': lang,
                },
            )
        }

    def __init__(self, *args, **kwargs):
        super(GalleryForm, self).__init__(*args, **kwargs)
        self.fields['image'].queryset = Photo.objects.filter(gallery=self.instance)
