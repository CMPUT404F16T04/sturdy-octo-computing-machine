# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-14 00:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('socknet', '0005_auto_20161103_0243'),
    ]

    operations = [
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('url', models.CharField(max_length=128, unique=b'True')),
            ],
        ),
    ]
