# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-18 23:56
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('socknet', '0010_auto_20161118_2241'),
    ]

    operations = [
        migrations.AddField(
            model_name='node',
            name='user',
            field=models.OneToOneField(default=0, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
