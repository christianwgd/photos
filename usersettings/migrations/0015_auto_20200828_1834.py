# Generated by Django 3.1 on 2020-08-28 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usersettings', '0014_usersettings_slide_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersettings',
            name='slide_time',
            field=models.PositiveSmallIntegerField(default=5, help_text='Zeit, die ein Bild angezeigt wird in Sekunden', verbose_name='Zeit Diashow'),
        ),
    ]
