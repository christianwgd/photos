from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from photos.models import Gallery, Photo


class Command(BaseCommand):
    help = 'Sync visibility of galleries for users from photos'

    def handle(self, *args, **options):
        galleries = Gallery.objects.all()
        for gallery in galleries:
            owners = Photo.objects.filter(gallery=gallery)\
                .order_by('owner')\
                .distinct('owner')\
                .values_list('owner', flat=True)
            for owner in owners:
                gallery.visible_for.add(User.objects.get(pk=owner))

            shared = Photo.objects.filter(gallery=gallery) \
                .order_by('shared') \
                .distinct('shared') \
                .values_list('shared', flat=True)
            for usr in shared:
                if usr is not None:
                    gallery.visible_for.add(User.objects.get(pk=usr))

        self.stdout.write(self.style.SUCCESS(
            'Visibility of gallery successfully synchronized'
        ))