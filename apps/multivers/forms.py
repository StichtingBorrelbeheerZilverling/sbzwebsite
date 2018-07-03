import json

from django.forms import forms, ModelForm

from apps.multivers import tools
from apps.multivers.models import Product


class FileForm(forms.Form):
    file = forms.FileField()

    def __init__(self, *args, **kwargs):
        self.cleaned_json = None
        super(FileForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(FileForm, self).clean()
        data = json.loads(cleaned_data['file'].read().decode('UTF-8'))
        error = tools.check_json_upload(data)
        if not error:
            self.cleaned_json = data
        else:
            self.add_error('file', 'Incorrect format. Missing or incorrect formatting:\n{}'.format(error))
        return cleaned_data


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['alexia_id', 'alexia_name', 'multivers_id', 'multivers_name', 'margin']
