import django_filters
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from .models import Photo, Event, Tag


class PhotoFilter(django_filters.FilterSet):
    event = django_filters.ModelChoiceFilter(
        queryset=Event.objects.all(),
        label = _('event')
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
    )
    timestamp = django_filters.DateFromToRangeFilter()
    uploaded = django_filters.DateFromToRangeFilter()
    uploaded_by = django_filters.ModelChoiceFilter(
        queryset=User.objects.all()
    )

    class Meta:
        model = Photo
        fields = ['event', 'tags', 'timestamp',
                  'uploaded', 'uploaded_by']