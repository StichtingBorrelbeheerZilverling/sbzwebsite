from django.db import models
from django.urls import reverse
from apps.moneybird.tools_moneybird import MoneybirdOrder, MoneybirdOrderLine, MoneybirdProduct


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
    moneybird_id = models.CharField(max_length=50, null=True, blank=True)
    vat_type = models.CharField(max_length=1, null=True, blank=False, choices=VAT_TYPE)

    def get_absolute_url(self):
        return reverse('moneybird:customer_update', args=(self.pk,))

    def __str__(self):
        return self.alexia_name

    class Meta:
        ordering = ['moneybird_id']


class ConceptOrder(models.Model):
    date = models.DateField()
    customer = models.ForeignKey("moneybird.Customer", on_delete=models.PROTECT)
    sent = models.BooleanField(default=False)

    def __str__(self):
        return "Concept Order for {} ({})".format(
            str(self.customer),
            self.date.strftime("%d-%m-%Y")
        )

    @property
    def reference(self):
        MONTHS = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]
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
            order_lines.append(MoneybirdOrderLine(description="{} - {}".format(self.name, line.product.moneybird_name),
                                                  product_id=line.product.moneybird_id,
                                                  quantity=line.amount))

        return order_lines

    class Meta:
        ordering = ['date', 'name']


class ConceptOrderDrinkLine(models.Model):
    drink = models.ForeignKey("moneybird.ConceptOrderDrink", models.CASCADE)
    product = models.ForeignKey("moneybird.Product", models.PROTECT)
    amount = models.FloatField()

    def __str__(self):
        return "{} for {}".format(str(self.product), str(self.drink))

    class Meta:
        ordering = ['product']

# TODO: Make sure that adding products also adds them to Moneybird
class Product(models.Model):
    alexia_id = models.IntegerField(unique=True)
    alexia_name = models.CharField(max_length=100, blank=False)
    moneybird_id = models.CharField(max_length=20, blank=True)
    moneybird_name = models.CharField(max_length=100, blank=True)

    def get_absolute_url(self):
        return reverse('moneybird:product_edit', args=(self.pk,))

    def __str__(self):
        return self.alexia_name
    
    def as_moneybird(self):
        return MoneybirdProduct(moneybird_id=self.moneybird_id, moneybird_name=self.moneybird_name)

    class Meta:
        ordering = ['moneybird_id']