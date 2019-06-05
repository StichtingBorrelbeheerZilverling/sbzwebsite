from django.contrib import admin

from apps.flowguard import models

admin.site.register(models.FlowChannel)
admin.site.register(models.FlowValue)
