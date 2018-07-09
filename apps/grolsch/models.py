import django
import os
from django.db import models

from apps.grolsch.scraping import DeKlok


class Product(models.Model):
    grolsch_article_no = models.CharField(max_length=255, blank=False, null=False)
    grolsch_name = models.CharField(max_length=255, blank=False, null=False)

    price_track_id = models.CharField(max_length=255, blank=False, null=True)
    last_price = models.PositiveIntegerField(null=True)
    last_discount_price = models.PositiveIntegerField(null=True)

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
    product = models.ForeignKey("grolsch.Product")
    new_price = models.PositiveIntegerField()
