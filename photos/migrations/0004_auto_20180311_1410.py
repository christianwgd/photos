# Generated by Django 2.0.3 on 2018-03-11 13:10

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0003_auto_20180311_1410'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='address',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default={}, null=True),
        ),
    ]
