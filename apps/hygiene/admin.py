from django.contrib import admin

from apps.hygiene import models

admin.site.register(models.CheckDay)
admin.site.register(models.CheckLocation)
admin.site.register(models.CheckItem)
admin.site.register(models.CheckDayItem)
