# Generated by Django 4.0.6 on 2022-07-13 06:58

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('photos', '0021_auto_20200828_1834'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Event',
            new_name='Gallery',
        ),
    ]
