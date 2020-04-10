from django.core.management.base import BaseCommand

from photos.models import Event, Import


class Command(BaseCommand):
    help = 'Removes empty Events and Imports'

    def handle(self, *args, **options):
        empty_events = Event.objects.filter(photo=None)
        ev_count = empty_events.count()
        empty_events.delete()
        empty_imports = Import.objects.filter(photo=None)
        imp_count = empty_imports.count()
        empty_imports.delete()

        self.stdout.write(self.style.SUCCESS(
            'Successfully deleted {events} Events and {imports} Imports'.format(
                events = ev_count,
                imports = imp_count
            )
        ))