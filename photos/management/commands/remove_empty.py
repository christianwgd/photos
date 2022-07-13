from django.core.management.base import BaseCommand

from photos.models import Gallery, Import


class Command(BaseCommand):
    help = 'Removes empty Galleries and Imports'

    def handle(self, *args, **options):
        empty_galleries = Gallery.objects.filter(photo=None)
        ev_count = empty_galleries.count()
        empty_galleries.delete()
        empty_imports = Import.objects.filter(photo=None)
        imp_count = empty_imports.count()
        empty_imports.delete()

        self.stdout.write(self.style.SUCCESS(
            'Successfully deleted {galleries} Galleries and {imports} Imports'.format(
                galleries = ev_count,
                imports = imp_count
            )
        ))