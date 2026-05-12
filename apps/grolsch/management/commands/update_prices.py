from django.core.management import BaseCommand

from apps.grolsch.models import Product, UnresolvedPriceChange
from apps.grolsch.tools import DeKlok


class Command(BaseCommand):
    help = 'Updates prices of all Grolsch products'

    def handle(self, *args, **options):
        UnresolvedPriceChange.objects.all().delete()

        products = Product.objects.all()
        ids = list(products.values_list('grolsch_id', flat=True))

        klok = DeKlok()
        klok_products = klok.get_product_prices(ids)

        for klok_product in klok_products:
            id = klok_product["id"]
            product = products.filter(grolsch_id=id).first()
            price = int(round(100*klok_product["price"]["actual"]["amount"]))

            if product.last_price != price and product.last_discount_price != price:
                change = UnresolvedPriceChange()
                change.product = product
                change.new_price = price
                change.save()
                change.mail()
                
            elif product.last_price == price:
                product.last_discount_price = None
                product.save()
