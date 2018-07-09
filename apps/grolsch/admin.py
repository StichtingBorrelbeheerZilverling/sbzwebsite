from django.contrib import admin

from apps.grolsch import models

admin.site.register(models.Product)
admin.site.register(models.UnresolvedPriceChange)
