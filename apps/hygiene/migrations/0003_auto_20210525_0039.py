# Generated by Django 2.2.23 on 2021-05-24 22:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hygiene', '0002_auto_20190618_1521'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checkday',
            name='checker',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
    ]