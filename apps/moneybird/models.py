from django.db import models
from django.urls import reverse
from apps.moneybird.tools_moneybird import MoneybirdOrder, MoneybirdOrderLine


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

    @staticmethod
    def get(setting):
        setting = Settings.objects.filter(key=setting).first()
        return setting.value if setting is not None else None

    @staticmethod
    def set(setting, value):
        setting, _ = Settings.objects.get_or_create(key=setting)
        setting.value = value
        setting.save()


class Customer(models.Model):
    VAT_TYPE = (
        ('0', 'Exclusief BTW'),
        ('1', 'Inclusief BTW'),
    )

    alexia_name = models.CharField(max_length=100, blank=False, unique=True)
    moneybird_id = models.CharField(max_length=18, blank=True, null=False)
    vat_type = models.CharField(max_length=1, blank=True, choices=VAT_TYPE)

    def get_absolute_url(self):
        return reverse('moneybird:customer_edit', args=(self.pk,))

    def __str__(self):
        return self.alexia_name
    
    def as_moneybird_dict(self):
        return {
            "company_name": self.alexia_name,
        }

    class Meta:
        ordering = ['alexia_name']


class ConceptOrder(models.Model):
    date = models.DateField()
    customer = models.ForeignKey("moneybird.Customer", on_delete=models.PROTECT)

    def __str__(self):
        return "Concept Order for {} ({})".format(
            str(self.customer),
            self.date.strftime("%d-%m-%Y")
        )

    @property
    def reference(self):
        first = self.conceptorderdrink_set.first()
        last = self.conceptorderdrink_set.last()

        first_month = first.date.strftime("%B")
        last_month = last.date.strftime("%B")

        if first_month == last_month:
            return "Borrels {}".format(first_month)
        else:
            return "Borrels {} - {}".format(first_month, last_month)

    def as_moneybird(self):
        result = MoneybirdOrder(reference=self.reference,
                                contact_id=self.customer.moneybird_id,
                                customer_vat_type=self.customer.vat_type)

        for drink in self.conceptorderdrink_set.all():
            for line in drink.as_moneybird():
                result.add_line(line)

        return result

    class Meta:
        ordering = ['date', 'customer']


class ConceptOrderDrink(models.Model):
    order = models.ForeignKey("moneybird.ConceptOrder", on_delete=models.CASCADE)
    date = models.DateField()
    name = models.CharField(max_length=255)
    locations = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def as_moneybird(self):
        period = self.date.strftime("%Y%m%d..%Y%m%d")
        order_lines = []

        for line in self.conceptorderdrinkline_set.all():
            order_lines.append(MoneybirdOrderLine(description="{} - {}".format(self.name, line.product.alexia_name),
                                                  product_id=line.product.moneybird_id,
                                                  quantity=line.amount,
                                                  period=period))

        return order_lines

    class Meta:
        ordering = ['date', 'name']


class ConceptOrderDrinkLine(models.Model):
    drink = models.ForeignKey("moneybird.ConceptOrderDrink", on_delete=models.CASCADE)
    product = models.ForeignKey("moneybird.Product", on_delete=models.PROTECT)
    amount = models.FloatField()

    def __str__(self):
        return "{} for {}".format(str(self.product), str(self.drink))

    class Meta:
        ordering = ['product']


class Product(models.Model):
    alexia_id = models.IntegerField(unique=True)
    alexia_name = models.CharField(max_length=100, blank=False)
    moneybird_id = models.CharField(max_length=18, blank=True)
    product_type = models.ForeignKey("moneybird.ProductType", on_delete=models.PROTECT, blank=True, null=True)

    def get_absolute_url(self):
        return reverse('moneybird:product_edit', args=(self.pk,))

    def __str__(self):
        return self.alexia_name
    
    def as_moneybird_dict(self):
        return {
            "price": 0,  # Moneybird requires a price
            "ledger_account_id": self.product_type.ledger_account_id,
            "title": self.alexia_name,
            "tax_rate_id": self.product_type.vat_rate.moneybird_id,
        }

    class Meta:
        ordering = ['alexia_id']


class ProductType(models.Model):
    name = models.CharField(max_length=255, unique=True, blank=False)
    ledger_account_id = models.CharField(max_length=18, blank=True)
    vat_rate = models.ForeignKey("moneybird.VatRate", on_delete=models.PROTECT, blank=False)

    def get_absolute_url(self):
        return reverse('moneybird:product_type_edit', args=(self.pk,))

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class VatRate(models.Model):
    vat_rate = models.CharField(max_length=40, unique=True, blank=False)
    moneybird_id = models.CharField(max_length=18, blank=False)

    def __str__(self):
        return self.vat_rate

    class Meta:
        ordering = ['vat_rate']
