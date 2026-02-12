import json
from datetime import datetime

from django.core.cache import cache
from django.forms import ModelForm, ChoiceField, HiddenInput, MultipleChoiceField, ModelMultipleChoiceField, \
    Form, CharField
from django.utils.functional import cached_property
from django import forms

from apps.multivers import tools_multivers
from apps.multivers.models import Product, ConceptOrder, ConceptOrderDrink, ConceptOrderDrinkLine, Location
from apps.util.forms import CachingModelMultipleChoiceField, CachingModelChoiceField


class FileForm(forms.Form):
    file = forms.FileField()

    def __init__(self, *args, **kwargs):
        self.cleaned_json = None
        super(FileForm, self).__init__(*args, **kwargs)

    def _validate_json(self, d):
        if not isinstance(d, dict):
            return "the top level element should be a dictionary."

        if not set(d.keys()) == {"products", "drinks"}:
            return "the top level element should only contain keys 'products' and 'drinks'."

        if not isinstance(d['products'], dict):
            return "the products key should contain a dictionary."

        for k, v in d['products'].items():
            if not isinstance(v, str):
                return "the products dictionary should only contain string values"

        product_ids = set(d['products'].keys())

        if not isinstance(d['drinks'], dict):
            return "the drinks key should contain a dictionary"

        for k, v in d['drinks'].items():
            if not isinstance(v, list):
                return "the drinks dictionary should only contain list values (key: {})".format(k)

            for i, drink in enumerate(v):
                if not isinstance(drink, dict):
                    return "the drinks dictionary should only contain list values that contain dictionaries " \
                           "(key: {}, list item {})".format(k, i)

                if not set(drink.keys()) == {'location', 'drink_name', 'date', 'products'}:
                    return "drink dictionaries should only contain the keys 'location', 'drink_name', 'date' and " \
                           "'prodcuts' (key: {}, list item {})".format(k, i)

                if not isinstance(drink['drink_name'], str):
                    return "drink names should be of type string (key: {}, list item {})".format(k, i)

                if not isinstance(drink['date'], str):
                    return "drink dates should be of type string (key: {}, list item {})".format(k, i)

                try:
                    datetime.strptime(drink['date'], '%d-%m-%Y')
                except ValueError:
                    return "drink dates should be of the format dd-mm-yyyy (key: {}, list item{})".format(k, i)

                if not isinstance(drink['location'], list):
                    return "drink location should be a list of strings (key: {}, list item {})".format(k, i)

                if not isinstance(drink['products'], dict):
                    return "drink products should be a dictionary (key: {}, list item {})".format(k, i)

                for j, location in enumerate(drink['location']):
                    if not isinstance(location, str):
                        return "drink location should only contain strings (key: {}, list item {}, location {})".format(k, i, j)

                for product_id, amount in drink['products'].items():
                    if product_id not in product_ids:
                        return "product id {} is not defined in the products dict".format(product_id)

                    try:
                        float(amount)
                    except ValueError:
                        return "amount should be a float value (key: {}, list item {}, product id {})".format(k, i, product_id)

    def clean(self):
        cleaned_data = super(FileForm, self).clean()

        if 'file' not in cleaned_data or self.has_error('file'):
            return cleaned_data

        try:
            data = json.loads(cleaned_data['file'].read().decode('utf-8'))
        except UnicodeDecodeError:
            self.add_error('file', 'Incorrect format: the file is not in utf-8.')
        except json.JSONDecodeError as e:
            self.add_error('file', 'Incorrect format: the file does not contain valid JSON.')
        else:
            error = self._validate_json(data)

            if error:
                self.add_error('file', 'Incorrect format: ' + error)
            else:
                self.cleaned_json = data

        return cleaned_data

    class Meta:
        model = ConceptOrder


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['alexia_id', 'alexia_name', 'multivers_id', 'multivers_name', 'moneybird_id', 'moneybird_name', 'margin']


class ConceptOrderDrinkForm(ModelForm):
    locations = CachingModelMultipleChoiceField(queryset=Location.objects)

    class Meta:
        model = ConceptOrderDrink
        fields = ['name', 'date', 'locations']


class ConceptOrderDrinkLineForm(ModelForm):
    product = CachingModelChoiceField(queryset=Product.objects)

    class Meta:
        model = ConceptOrderDrinkLine
        fields = ['product', 'amount']


class SendOrdersForm(Form):
    override_revenue_account = CharField(max_length=255, required=False)
