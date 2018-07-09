from django import forms


class CreateProductFromUrlForm(forms.Form):
    url = forms.URLField()
    track_price = forms.BooleanField()
