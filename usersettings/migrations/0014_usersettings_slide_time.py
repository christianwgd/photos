# Generated by Django 3.0.6 on 2020-05-18 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usersettings', '0013_auto_20200324_1134'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersettings',
            name='slide_time',
            field=models.PositiveSmallIntegerField(default=5, help_text='Time one slide is shown in seconds', verbose_name='Slideshow time'),
        ),
    ]
