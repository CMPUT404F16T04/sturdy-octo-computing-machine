# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-22 07:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('socknet', '0015_merge_20161021_2245'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Image',
            new_name='ImageServ',
        ),
    ]
