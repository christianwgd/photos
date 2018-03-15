# Generated by Django 2.0.3 on 2018-03-15 08:36

from django.db import migrations, models
import photos.models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0008_import_slug'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='import',
            options={'ordering': ['-timestamp'], 'verbose_name': 'import', 'verbose_name_plural': 'imports'},
        ),
        migrations.AlterField(
            model_name='photo',
            name='thumb',
            field=models.ImageField(blank=True, max_length=255, null=True, upload_to=photos.models.thumb_path, verbose_name='thumbnail'),
        ),
    ]
