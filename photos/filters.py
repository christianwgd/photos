import django_filters

from .models import Photo, Event, Tag


class PhotoFilter(django_filters.FilterSet):
    event = django_filters.ModelChoiceFilter(queryset=Event.objects.all())
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all())
    timestamp = django_filters.DateRangeFilter()
    uploaded = django_filters.DateRangeFilter()
    uploaded_by__username = django_filters.AllValuesFilter()

    class Meta:
        model = Photo
        fields = ['event', 'tags', 'timestamp',
                  'uploaded', 'uploaded_by__username']
