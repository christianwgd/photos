# -*- coding: utf-8 -*-
from django.db.models import Manager, Q


class PhotoVisibleManager(Manager):

    def visible(self, for_user=None):
        return self.filter(
            Q(owner=for_user) |
            Q(shared=for_user)
        )


class EventVisibleManager(Manager):

    def visible(self, for_user=None):
        return self.filter(
            visible_for=for_user
        )


