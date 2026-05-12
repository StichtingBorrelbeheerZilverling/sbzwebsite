import django
import os
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse

from apps.grolsch.scraping import DeKlok
from settings import FULL_URL_PREFIX


class Product(models.Model):
    grolsch_article_no = models.CharField(max_length=255, blank=False, null=False)
    grolsch_name = models.CharField(max_length=255, blank=False, null=False)

    price_track_id = models.CharField(max_length=255, blank=True, null=True)
    last_price = models.PositiveIntegerField(null=True, blank=True)
    last_discount_price = models.PositiveIntegerField(null=True, blank=True)

    @property
    def last_price_str(self):
        return None if self.last_price is None else "{:.2f}".format(self.last_price / 100)

    @property
    def last_discount_price_str(self):
        return None if self.last_discount_price is None else "{:.2f}".format(self.last_discount_price / 100)

    def __str__(self):
        return self.grolsch_name

    @staticmethod
    def str_to_cents(s):
        euros, cents = s.split(".")
        return int(euros) * 100 + int(cents)

    @staticmethod
    def create_from_url(url, track_price):
        klok = DeKlok()
        product = Product()
        product.grolsch_article_no = klok.get_article_no_by_url(url)
        product.grolsch_name = klok.get_article_name_by_url(url)

        if track_price:
            product.price_track_id = klok.get_pid_by_url(url)
            prices = klok.get_product_prices([product.price_track_id])
            product.last_price = Product.str_to_cents(prices[product.price_track_id]['price'])
            product.last_discount_price = None

        return product


class UnresolvedPriceChange(models.Model):
    product = models.ForeignKey("grolsch.Product", on_delete=models.CASCADE)
    new_price = models.PositiveIntegerField()

    @property
    def new_price_str(self):
        return None if self.new_price is None else "{:.2f}".format(self.new_price / 100)

    def __str__(self):
        return "{} to {}".format(
            str(self.product),
            self.new_price_str
        )

    def get_absolute_url(self):
        return reverse('grolsch:price_change_detail', args=[self.pk])

    def mail(self):
        context = {
            'change': self,
            'full_url': FULL_URL_PREFIX + self.get_absolute_url()
        }

        html = render_to_string('grolsch/mail/price_change.html', context)
        plain = render_to_string('grolsch/mail/price_change.txt', context)

        send_mail(subject='[SBZ] Price change of {}'.format(str(self.product)),
                  message=plain,
                  html_message=html,
                  from_email='www@sbz.utwente.nl',
                  recipient_list=['bestellingen@sbz.utwente.nl'])
