from __future__ import unicode_literals

from django.db import models
from django.urls import reverse


class Settings(models.Model):
    key = models.CharField(max_length=100, null=False, blank=False, primary_key=True)
    value = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['key']
        verbose_name = 'Setting'
        verbose_name_plural = 'Settings'

    def __str__(self):
        if self.value:
            return "{}: \"{:20s}\"".format(self.key, self.value)
        else:
            return "{}: Not set".format(self.key)

    def get_absolute_url(self):
        return reverse('multivers:settings_update', args=(self.pk,))


class Product(models.Model):
    NO_MARGIN = 0
    HAS_MARGIN = 1
    MARGIN = (
        (NO_MARGIN, 'No margin'),
        (HAS_MARGIN, 'Has margin')
    )

    alexia_id = models.IntegerField(unique=True)
    alexia_name = models.CharField(max_length=100, blank=False)
    multivers_id = models.CharField(max_length=20, blank=False)
    multivers_name = models.CharField(max_length=100, blank=False)
    margin = models.IntegerField(choices=MARGIN, default=HAS_MARGIN)

    def get_absolute_url(self):
        return reverse('multivers:product_update', args=(self.pk,))

    def __str__(self):
        return self.alexia_name

    class Meta:
        ordering = ('alexia_name',)


class Costumer(models.Model):
    VAT_TYPE = (
        ('0', 'Exclusief BTW'),
        ('1', 'Inclusief BTW'),
    )

    alexia_name = models.CharField(max_length=100, blank=False, unique=True)
    multivers_id = models.CharField(max_length=50, null=True, blank=False)
    vat_type = models.CharField(max_length=1, null=True, blank=False, choices=VAT_TYPE)

    def get_absolute_url(self):
        return reverse('multivers:costumer_update', args=(self.pk,))

    def __str__(self):
        return self.alexia_name


class Location(models.Model):
    NO_DISCOUNT = 0
    EXCLUSIVE_DISCOUNT = 1
    ALWAYS_DISCOUNT = 2
    DISCOUNT_TYPE = (
        (0, 'No discount'),
        (1, 'Discount if exclusive'),
        (2, 'Always discount'),
    )

    name = models.CharField(max_length=100, blank=False, unique=True)
    no_discount = models.IntegerField(choices=DISCOUNT_TYPE, null=True)

    def get_absolute_url(self):
        return reverse('multivers:location_update', args=(self.pk,))
