# -*- coding: utf-8 -*-
from django.db.models import Manager, Q


class PhotoVisibleManager(Manager):

    def visible(self, for_user=None):
        return self.filter(
            Q(owner=for_user) |
            Q(shared=for_user)
        )

    def shared(self, for_user=None):
        return self.filter(
            owner=for_user,
            shared__isnull=False
        )


class EventVisibleManager(Manager):

    def visible(self, for_user=None):
        if for_user is None:
            return self.all()
        return self.filter(
            visible_for=for_user
        )



