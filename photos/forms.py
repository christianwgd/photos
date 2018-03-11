# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django import forms
from .models import Photo


class PhotoForm(forms.ModelForm):

    select = forms.BooleanField()

    class Meta:
        model = Photo
        fields = ('select',)


PhotoFormSet = forms.modelformset_factory(Photo, form=PhotoForm, extra=0)


class UploadForm(forms.Form):

    event = forms.CharField(label=_('event'), max_length=255, required=False)
    tags = forms.CharField(label=_('tags'), max_length=255, required=False)

