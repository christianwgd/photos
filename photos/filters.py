import django_filters
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django_filters.widgets import RangeWidget

from .models import Photo, Gallery, Tag


class PhotoFilter(django_filters.FilterSet):
    class Meta:
        model = Photo
        fields = [
            'gallery', 'tags', 'timestamp',
            'uploaded', 'uploaded_by', 'upload'
        ]

    gallery = django_filters.ModelChoiceFilter(
        queryset=Gallery.objects.all(),
        label=_('gallery'),
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
    )
    timestamp = django_filters.DateFromToRangeFilter(
        widget=RangeWidget(attrs={'type': 'date'})
    )
    uploaded = django_filters.DateFromToRangeFilter(
        widget=RangeWidget(attrs={'type': 'date'})
    )
    uploaded_by = django_filters.ModelChoiceFilter(
        queryset=User.objects.all()
    )

    order = django_filters.OrderingFilter(
        choices=(
            ('gallery', _('gallery')),
            ('uploaded', _('Uploaded')),
            ('timestamp', _('Timestamp'))
        ),
    )

    def __init__(self, request, *args, **kwargs):
        super(PhotoFilter, self).__init__(*args, **kwargs)
        self.filters['gallery'].queryset = Gallery.objects.visible(
            for_user=request.user
        )
    