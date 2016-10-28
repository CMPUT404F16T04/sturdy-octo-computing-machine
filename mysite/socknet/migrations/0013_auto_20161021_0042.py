# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-21 06:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('socknet', '0012_auto_20161020_2300'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='parent_post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comment_parent_post', to='socknet.Post'),
        ),
    ]