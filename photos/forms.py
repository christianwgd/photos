# -*- coding: utf-8 -*-

from django import forms
from .models import Photo


class PhotoForm(forms.ModelForm):

    select = forms.BooleanField()

    class Meta:
        model = Photo
        fields = ('select',)


PhotoFormSet = forms.modelformset_factory(Photo, form=PhotoForm, extra=0)
