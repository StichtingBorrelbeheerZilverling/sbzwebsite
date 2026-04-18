from django.contrib import admin

from . import models


class SettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    list_editable = ('value',)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('alexia_id', 'alexia_name', 'moneybird_id', 'product_type')
    list_editable = ('moneybird_id', 'product_type')


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('alexia_name','moneybird_id','vat_type')
    list_editable = ('moneybird_id', 'vat_type')


admin.site.register(models.Settings, SettingsAdmin)
admin.site.register(models.Product, ProductAdmin)
admin.site.register(models.Customer, CustomerAdmin)

admin.site.register(models.ConceptOrder)
admin.site.register(models.ConceptOrderDrink)
admin.site.register(models.ConceptOrderDrinkLine)
