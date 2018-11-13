from django.core.validators import RegexValidator
from django.db import models


class Group(models.Model):
    TYPES = [
        ("O", "Organization"),
        ("F", "Function"),
        ("P", "Person"),
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=1, choices=TYPES)
    group_destinations = models.ManyToManyField("mail.Group", blank=True, related_name="group_origins")

    outgoing_email = models.EmailField(null=True, blank=True)
    incoming_aliases = models.CharField(max_length=255, blank=True, validators=[RegexValidator("[a-z0-9-_,]*")])

    @property
    def incoming_aliases_list(self):
        return [] if self.incoming_aliases == "" else self.incoming_aliases.split(",")

    @property
    def iconic_icon(self):
        return {
            'O': 'people',
            'F': 'briefcase',
            'P': 'person',
        }[self.type]

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("type", "name")
