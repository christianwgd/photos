# -*- coding: utf-8 -*-
from django.db.models import Manager, Q


class PhotoVisibleManager(Manager):
    """
    For non-staff users, return items with a visible status.
    """

    def visible(self, for_user=None):
        return self.filter(
            Q(owner=for_user) |
            Q(shared=for_user)
        )


# TODO: Visible manager for events??