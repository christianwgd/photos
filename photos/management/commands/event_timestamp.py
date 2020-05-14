from django.core.management.base import BaseCommand

from photos.models import Event


class Command(BaseCommand):
    help = 'Add event timestamp for events without one'

    def handle(self, *args, **options):
        events = Event.objects.all()
        count = 0
        for event in events:
            if event.timestamp is None:
                photos = event.photo_set.all()
                latest = photos.latest('timestamp')
                event.timestamp = latest.timestamp
                event.save()
                count += 1

        self.stdout.write(self.style.SUCCESS(
            'Timestamp of {count} events successfully synchronized'.format(
                count=count
            )
        ))