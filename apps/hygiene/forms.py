from django import forms
from django.contrib.auth.models import User

from apps.hygiene.models import CheckDay, CheckDayItem, CheckItem


class CheckDayForm(forms.ModelForm):
    date = forms.DateField(widget=forms.HiddenInput())
    checker = forms.ModelChoiceField(queryset=User.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        self.declared_fields['checker'].label_from_instance = lambda obj: obj.get_full_name()
        super(CheckDayForm, self).__init__(*args, **kwargs)

    class Meta:
        fields = ['date', 'checker']
        model = CheckDay


class CheckDayCommentsForm(forms.ModelForm):
    class Meta:
        fields = ['comments']
        model = CheckDay


class CheckDayItemForm(forms.ModelForm):
    class Meta:
        model = CheckDayItem
        fields = ['result']
