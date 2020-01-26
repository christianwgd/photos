# -*- coding: utf-8 -*-
from django.db.models import Manager, Q


class VisibleManager(Manager):
    """
    For non-staff users, return items with a visible status.
    """

    def visible(self, for_user=None):
        return self.filter(
            Q(uploaded_by=for_user) |
            Q(shared=for_user)
        )
