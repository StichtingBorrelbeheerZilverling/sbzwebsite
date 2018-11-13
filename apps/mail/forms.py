from django import forms

from apps.mail import models


class GroupForm(forms.ModelForm):
    class Meta:
        model = models.Group
        fields = ['name', 'type', 'group_destinations', 'outgoing_email', 'incoming_aliases']
