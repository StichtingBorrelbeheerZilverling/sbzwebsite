from django import forms


class CreateProductFromUrlForm(forms.Form):
    url = forms.URLField()
    track_price = forms.BooleanField()


class PriceChangeResolveForm(forms.Form):
    CHOICE_NEW_PRICE = 'NEW'
    CHOICE_DISCOUNT_PRICE = 'DISCOUNT'

    CHOICES = [
        (CHOICE_NEW_PRICE, "This is the new price of the product"),
        (CHOICE_DISCOUNT_PRICE, "This price is a temporary discount"),
    ]

    price_change_type = forms.ChoiceField(choices=CHOICES)
