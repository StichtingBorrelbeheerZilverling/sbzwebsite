from django.core import mail
from django.core.management import BaseCommand

from apps.grolsch.models import Product, UnresolvedPriceChange
from apps.grolsch.scraping import DeKlok


class Command(BaseCommand):
    help = 'Updates prices of all price-tracked Grolsch products'

    def handle(self, *args, **options):
        UnresolvedPriceChange.objects.all().delete()

        products = Product.objects.filter(price_track_id__isnull=False).all()
        pids = list(products.values_list('price_track_id', flat=True))

        klok = DeKlok()
        prices = klok.get_product_prices(pids)

        for product in products:
            price = Product.str_to_cents(prices[product.price_track_id]['price'])

            if product.last_price != price and product.last_discount_price != price:
                change = UnresolvedPriceChange()
                change.product = product
                change.new_price = price
                change.save()

                change.mail()
            elif product.last_price == price:
                product.last_discount_price = None
                product.save()
