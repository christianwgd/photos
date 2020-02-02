# Generated by Django 3.0.2 on 2020-01-30 15:10

from django.db import migrations
import filebrowser.fields


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0015_auto_20200127_2004'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='photo',
            name='thumb',
        ),
        migrations.AlterField(
            model_name='photo',
            name='imagefile',
            field=filebrowser.fields.FileBrowseField(blank=True, max_length=255, verbose_name='file'),
        ),
    ]