from django import template
from django.forms import fields
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def bootstrap_form(form):
    return mark_safe(render_to_string("bootstrap_form/form.html", {"form": form}))


def _bootstrap_form_field_template(field):
    if isinstance(field.field, fields.IntegerField):
        return "bootstrap_form/field_integer.html"
    elif isinstance(field.field, fields.CharField):
        return "bootstrap_form/field_text.html"
    elif isinstance(field.field, fields.TypedChoiceField):
        return "bootstrap_form/field_choice.html"
    else:
        return "bootstrap_form/field_default.html"


@register.filter
def bootstrap_form_field(field):
    template = _bootstrap_form_field_template(field)
    return mark_safe(render_to_string(template, {"field": field}))


@register.filter
def bootstrap_form_errors(errors):
    return mark_safe(render_to_string("bootstrap_form/form_errors.html", {"errors": errors}))
