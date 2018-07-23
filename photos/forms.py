# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django import forms
from .models import Photo, Event


class PhotoForm(forms.ModelForm):

    class Meta:
        model = Photo
        fields = ('name', 'event', 'tags', 'latitude', 'longitude')


PhotoFormSet = forms.modelformset_factory(Photo, form=PhotoForm, extra=0)


class UploadForm(forms.Form):

    event = forms.CharField(label=_('event'), max_length=255, required=False)
    tags = forms.CharField(label=_('tags'), max_length=255, required=False)

