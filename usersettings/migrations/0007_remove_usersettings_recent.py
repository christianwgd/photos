# Generated by Django 3.0.3 on 2020-03-02 08:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usersettings', '0006_auto_20200205_1858'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usersettings',
            name='recent',
        ),
    ]
