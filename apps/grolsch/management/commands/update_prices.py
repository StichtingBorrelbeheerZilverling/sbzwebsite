import math
from django.core import mail
from django.core.management import BaseCommand

from apps.grolsch.models import Product, UnresolvedPriceChange
from apps.grolsch.scraping import DeKlok


class Command(BaseCommand):
    help = 'Updates prices of all price-tracked Grolsch products'

    def handle(self, *args, **options):
        UnresolvedPriceChange.objects.all().delete()

        products = Product.objects.filter(price_track_id__isnull=False).all()
        skus = list(products.values_list('grolsch_article_no', flat=True))

        klok = DeKlok()
        prices = klok.get_product_prices(skus)

        for product, price in zip(products, prices['result']):
            price = int(round(100*price['price']))

            if product.last_price != price and product.last_discount_price != price:
                change = UnresolvedPriceChange()
                change.product = product
                change.new_price = price
                change.save()

                change.mail()
            elif product.last_price == price:
                product.last_discount_price = None
                product.save()
