from django.contrib import admin

from . import models


class SettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    list_editable = ('value',)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('alexia_id', 'alexia_name', 'multivers_id', 'multivers_name', 'margin')
    list_editable = ('multivers_id', 'multivers_name', 'margin')


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('alexia_name', 'multivers_id', 'vat_type')
    list_editable = ('multivers_id', 'vat_type')


admin.site.register(models.Settings, SettingsAdmin)
admin.site.register(models.Product, ProductAdmin)
admin.site.register(models.Customer, CustomerAdmin)
