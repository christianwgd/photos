import django_filters
from django.contrib.auth.models import User
from django_select2 import forms

from .models import Photo, Event, Tag


class PhotoFilter(django_filters.FilterSet):
    event = django_filters.ModelChoiceFilter(
        queryset=Event.objects.all(),
        widget=forms.Select2Widget
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        widget=forms.Select2MultipleWidget,
    )
    timestamp = django_filters.DateRangeFilter()
    uploaded = django_filters.DateRangeFilter()
    uploaded_by = django_filters.ModelChoiceFilter(
        queryset=User.objects.all()
    )

    class Meta:
        model = Photo
        fields = ['event', 'tags', 'timestamp',
                  'uploaded', 'uploaded_by']
