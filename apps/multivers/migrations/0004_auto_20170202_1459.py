# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-02 13:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multivers', '0003_auto_20170202_1454'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='alexia_name',
            field=models.CharField(max_length=100),
        ),
    ]
