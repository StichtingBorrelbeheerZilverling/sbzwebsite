from __future__ import unicode_literals

from django.db import models


class Settings(models.Model):
    key = models.CharField(max_length=100, null=False,
                           blank=False, primary_key=True)
    value = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['key']
        verbose_name = 'Instelling'
        verbose_name_plural = 'Instellingen'

    def __str__(self):
        return "{}: \"{:20s}\"".format(self.key, self.value)
