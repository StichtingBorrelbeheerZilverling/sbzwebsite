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
        return reverse('multivers:product_edit', args=(self.pk,))

    def __str__(self):
        return self.alexia_name

    class Meta:
        ordering = ('multivers_id',)


class Customer(models.Model):
    VAT_TYPE = (
        ('0', 'Exclusief BTW'),
        ('1', 'Inclusief BTW'),
    )

    alexia_name = models.CharField(max_length=100, blank=False, unique=True)
    multivers_id = models.CharField(max_length=50, null=True, blank=False)
    vat_type = models.CharField(max_length=1, null=True, blank=False, choices=VAT_TYPE)

    def get_absolute_url(self):
        return reverse('multivers:customer_update', args=(self.pk,))

    def __str__(self):
        return self.alexia_name

    class Meta:
        ordering = ['multivers_id']


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

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class ConceptOrder(models.Model):
    date = models.DateField()
    customer = models.ForeignKey("multivers.Customer", on_delete=models.PROTECT)

    def __str__(self):
        return "Concept Order for {} ({})".format(
            str(self.customer),
            self.date.strftime("%d-%m-%Y")
        )

    @property
    def reference(self):
        MONTHS = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober",
                  "november", "december"]
        first = self.conceptorderdrink_set.first()
        last = self.conceptorderdrink_set.last()

        first_month = MONTHS[first.date.month - 1]
        last_month = MONTHS[last.date.month - 1]

        if first_month == last_month:
            return "Borrels {}".format(first_month)
        else:
            return "Borrels {} - {}".format(first_month, last_month)

    def as_multivers(self, revenue_account=None):
        from apps.multivers.tools import MultiversOrder
        result = MultiversOrder(date=self.date,
                                reference=self.reference,
                                payment_condition_id=Settings.get('payment_condition'),
                                customer_id=self.customer.multivers_id,
                                customer_vat_type=self.customer.vat_type,
                                processor_id=Settings.get('processor_id'),
                                processor_name=Settings.get('processor_name'))

        for drink in self.conceptorderdrink_set.all():
            for line in drink.as_multivers(revenue_account=revenue_account):
                result.add_line(line)

        return result

    class Meta:
        ordering = ['date', 'customer']


class ConceptOrderDrink(models.Model):
    order = models.ForeignKey("multivers.ConceptOrder", on_delete=models.PROTECT)
    date = models.DateField()
    name = models.CharField(max_length=255)
    locations = models.ManyToManyField("multivers.Location")

    sent = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def as_multivers(self, revenue_account=None):
        from apps.multivers.tools import MultiversOrderLine
        order_lines = []

        discount_amount = float(Settings.get('discount')) / 100.0
        discount_location = self.locations.filter(no_discount=Location.ALWAYS_DISCOUNT).exists() or \
                            not self.locations.filter(no_discount=Location.NO_DISCOUNT)

        for line in self.conceptorderdrinkline_set.all():
            discount = discount_location and line.product.margin == Product.HAS_MARGIN

            order_lines.append(MultiversOrderLine(date=self.date,
                                                  description="{} - {}".format(self.name, line.product.multivers_name),
                                                  discount=discount_amount if discount else 0.0,
                                                  product_id=line.product.multivers_id,
                                                  quantity=line.amount,
                                                  revenue_account=revenue_account if revenue_account else None))

        return order_lines

    class Meta:
        ordering = ['date', 'name']


class ConceptOrderDrinkLine(models.Model):
    drink = models.ForeignKey("multivers.ConceptOrderDrink", models.CASCADE)
    product = models.ForeignKey("multivers.Product", models.PROTECT)
    amount = models.FloatField()

    def __str__(self):
        return "{} for {}".format(str(self.product), str(self.drink))

    class Meta:
        ordering = ['product']
