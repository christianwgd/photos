from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from photos.models import Event, Photo

class Command(BaseCommand):
    help = 'Sync visibility of events for users from photos'

    def handle(self, *args, **options):
        events = Event.objects.all()
        for event in events:
            owners = Photo.objects.filter(event=event)\
                .order_by('owner')\
                .distinct('owner')\
                .values_list('owner', flat=True)
            for owner in owners:
                event.visible_for.add(User.objects.get(pk=owner))

            shared = Photo.objects.filter(event=event) \
                .order_by('shared') \
                .distinct('shared') \
                .values_list('shared', flat=True)
            for usr in shared:
                if usr is not None:
                    event.visible_for.add(User.objects.get(pk=usr))

        self.stdout.write(self.style.SUCCESS(
            'Visibility of event successfully synchronized'
        ))