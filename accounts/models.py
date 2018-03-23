from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

# chris 5674e8d0c9408476f8b89dee85d4e08003649cfa
# bob 667594d84815c46eea4c38eb9a686010a1e1db66
# new_user 5f05673bd6ab749fe50832633249a201a13acdc5
# admin 93138ba960dfb4ef2eef6b907718ae04400f606a
