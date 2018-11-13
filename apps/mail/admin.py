from django.contrib import admin
from apps.mail import models


@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "outgoing_email")
