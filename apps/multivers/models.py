from __future__ import unicode_literals

from django.db import models


class Settings(models.Model):
    key = models.CharField(max_length=100, null=False, unique=True, blank=False)
    value = models.CharField(max_length=100)

    class Meta:
        ordering = ['key']
        verbose_name = 'Instelling'
        verbose_name_plural = 'Instellingen'
