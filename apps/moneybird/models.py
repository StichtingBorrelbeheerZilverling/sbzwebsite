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

    def get_absolute_url(self):
        return reverse('moneybird:settings_update', args=(self.pk,))


# TODO: Make sure that adding customers also adds them to Moneybird
class Customer(models.Model):
    VAT_TYPE = (
        ('0', 'Exclusief BTW'),
        ('1', 'Inclusief BTW'),
    )

    alexia_name = models.CharField(max_length=100, blank=False, unique=True)
    moneybird_id = models.CharField(max_length=18, blank=True, null=False)
    vat_type = models.CharField(max_length=1, blank=False, choices=VAT_TYPE, default='1')
    # self.invoice_workflow_id = invoice_workflow_id # Currently not supported

    def get_absolute_url(self):
        return reverse('moneybird:customer_update', args=(self.pk,))

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
    sent = models.BooleanField(default=False) # TODO: implement that this is used?

    def __str__(self):
        return "Concept Order for {} ({})".format(
            str(self.customer),
            self.date.strftime("%d-%m-%Y")
        )

    @property
    def reference(self):
        MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        first = self.conceptorderdrink_set.first()
        last = self.conceptorderdrink_set.last()

        first_month = MONTHS[first.date.month - 1]
        last_month = MONTHS[last.date.month - 1]

        if first_month == last_month:
            return "Borrels {}".format(first_month)
        else:
            return "Borrels {} - {}".format(first_month, last_month)

    def as_moneybird(self):
        result = MoneybirdOrder(reference=self.reference,
                                contact_id=int(self.customer.moneybird_id),
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
        order_lines = []

        for line in self.conceptorderdrinkline_set.all():
            # TODO: Rewrite to moneybird
            order_lines.append(MoneybirdOrderLine(description="{} - {}".format(self.name, line.product.alexia_name),
                                                  product_id=line.product.moneybird_id,
                                                  quantity=line.amount))

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


# TODO: Make sure that adding products also adds them to Moneybird
class Product(models.Model):
    alexia_id = models.IntegerField(unique=True)
    alexia_name = models.CharField(max_length=100, blank=False)
    moneybird_id = models.CharField(max_length=18, blank=True)
    product_type = models.ForeignKey("moneybird.ProductType", on_delete=models.PROTECT)

    def get_absolute_url(self):
        return reverse('moneybird:product_edit', args=(self.pk,))

    def __str__(self):
        return self.alexia_name
    
    # TODO: Implement automatic ledger_account_id based on type of drink
    def as_moneybird_dict(self):
        return {
            "price": 0,  # Moneybird requires a price
            "ledger_account_id": self.product_type.ledger_account_id, # Moneybird requires a ledger account id
            "title": self.alexia_name,
            "vat_rate_id": self.product_type.vat_rate.moneybird_id,
        }

    class Meta:
        ordering = ['alexia_id']


# TODO: make product types updatable/creatable/deletable
class ProductType(models.Model):
    PRODUCT_TYPES = (
        ('0', 'Bier'),
        ('1', 'Speciaalbier'),
        ('2', 'Wijn'),
        ('3', 'Fris'),
        ('4', 'Maltbier'),
        ('5', 'Snacks'),
        ('6', 'Speciaalbier van de maand'),
        ('7', 'Likeur'),
    )

    product_type = models.CharField(max_length=1, choices=PRODUCT_TYPES, unique=True, blank=False)
    ledger_account_id = models.CharField(max_length=18, blank=True)
    vat_rate = models.ForeignKey("moneybird.VatRate", on_delete=models.PROTECT)

    def __str__(self):
        return self.product_type

    class Meta:
        ordering = ['product_type']


class VatRate(models.Model):
    VAT_RATES = (
        ('0', '21%'),
        ('1', '9%'),
        ('2', '0%'),
        ('3', 'BTW vrijgesteld'),
    )

    vat_rate = models.CharField(max_length=1, choices=VAT_RATES, unique=True, blank=False)
    moneybird_id = models.CharField(max_length=18, blank=False)

    def __str__(self):
        return self.vat_rate

    class Meta:
        ordering = ['vat_rate']
