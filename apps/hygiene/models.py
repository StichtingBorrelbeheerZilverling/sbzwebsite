from django.db import models
from django.utils.translation import ugettext_lazy as _


class CheckDay(models.Model):
    date = models.DateField()
    checker = models.ForeignKey("auth.User")


class CheckLocation(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class CheckItem(models.Model):
    name = models.CharField(max_length=255)
    location = models.ForeignKey("hygiene.CheckLocation")

    def __str__(self):
        return "{} @ {}".format(self.name, self.location)


class CheckDayItem(models.Model):
    RESULT_CHOICES = [
        ('GOOD', _('✓')),
        ('ACCEPT', _('∼')),
        ('BAD', _('🗙')),
    ]

    item = models.ForeignKey("hygiene.CheckItem")
    day = models.ForeignKey("hygiene.CheckDay")
    result = models.CharField(max_length=8, choices=RESULT_CHOICES)
