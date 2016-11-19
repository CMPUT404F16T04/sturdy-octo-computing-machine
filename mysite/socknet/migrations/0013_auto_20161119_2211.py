# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-19 22:11
from __future__ import unicode_literals

from django.db import migrations

def forwards_func(apps, schema_editor):
    print("In forwards function")
    """
    Create an admin config model
    """
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    AdminConfig = apps.get_model("socknet", "AdminConfig")
    db_alias = schema_editor.connection.alias
    """
    AdminConfig.objects.using(db_alias).bulk_create([
        AdminConfig(name="USA", code="us"),
    ])
    """
    AdminConfig.objects.using(db_alias).create(url="http://127.0.0.1:8000/")

def reverse_func(apps, schema_editor):
    AdminConfig = apps.get_model("socknet", "AdminConfig")
    db_alias = schema_editor.connection.alias
    AdminConfig.objects.using(db_alias).filter(url="http://127.0.0.1:8000/").delete()

class Migration(migrations.Migration):

    dependencies = [
        ('socknet', '0012_adminconfig'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
