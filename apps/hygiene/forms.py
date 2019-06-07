from django import forms
from django.contrib.auth.models import User

from apps.hygiene.models import CheckDay, CheckDayItem, CheckItem


class CheckDayForm(forms.ModelForm):
    date = forms.DateField(widget=forms.HiddenInput())
    checker = forms.ModelChoiceField(queryset=User.objects.all(), required=False)

    class Meta:
        fields = ['date', 'checker']
        model = CheckDay


class CheckDayItemForm(forms.ModelForm):
    class Meta:
        model = CheckDayItem
        fields = ['result']
