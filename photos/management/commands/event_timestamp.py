from django.core.management.base import BaseCommand

from photos.models import Gallery, Photo


class Command(BaseCommand):
    help = 'Add gallery timestamp for galleries without one'

    def handle(self, *args, **options):
        galleries = Gallery.objects.all()
        count = 0
        for gallery in galleries:
            if gallery.timestamp is None:
                photos = gallery.photo_set.all()
                try:
                    latest = photos.latest('timestamp')
                    gallery.timestamp = latest.timestamp
                    gallery.save()
                    count += 1
                except Photo.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        'Gallery {gallery} has no photos with timestamp'.format(
                            gallery=gallery.name
                        )
                    ))

        self.stdout.write(self.style.SUCCESS(
            'Timestamp of {count} galleries successfully synchronized'.format(
                count=count
            )
        ))