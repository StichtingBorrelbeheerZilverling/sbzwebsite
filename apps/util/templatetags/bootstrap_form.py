from django import template
from django.forms import fields, ModelMultipleChoiceField, ModelChoiceField, BoundField
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def bootstrap_form(form):
    return mark_safe(render_to_string("bootstrap_form/form.html", {"form": form}))


def _bootstrap_form_field_template(field):
    if isinstance(field.field, fields.IntegerField):
        # Cast floats to string with dot decimal point
        field.initial_string = str(field.initial or "")
        return "bootstrap_form/field_number.html"
    elif isinstance(field.field, fields.CharField):
        return "bootstrap_form/field_text.html"
    elif isinstance(field.field, (fields.MultipleChoiceField, ModelMultipleChoiceField)):
        return "bootstrap_form/field_choice_multiple.html"
    elif isinstance(field.field, (fields.TypedChoiceField, ModelChoiceField,)):
        return "bootstrap_form/field_choice.html"
    elif isinstance(field.field, fields.FileField):
        return "bootstrap_form/field_file.html"
    elif isinstance(field.field, fields.DateField):
        return "bootstrap_form/field_date.html"
    elif isinstance(field.field, fields.BooleanField):
        return "bootstrap_form/field_bool.html"
    else:
        return "bootstrap_form/field_default.html"


@register.filter
def bootstrap_form_field(field):
    template = _bootstrap_form_field_template(field)
    return mark_safe(render_to_string(template, {"field": field}))


@register.filter
def bootstrap_form_errors(errors):
    return mark_safe(render_to_string("bootstrap_form/form_errors.html", {"errors": errors}))


@register.simple_tag(takes_context=True)
def bootstrap_edit_modal(context, obj, form, action, *args):
    return mark_safe(render_to_string("bootstrap_form/modal_edit.html", {
        "form": form,
        "obj": obj,
        "action": reverse(action, args=args),
        "csrf_token": context.get("csrf_token", None),
    }))


@register.simple_tag(takes_context=True)
def bootstrap_delete_modal(context, obj, action, *args):
    return mark_safe(render_to_string("bootstrap_form/modal_delete.html", {
        "obj": obj,
        "action": reverse(action, args=args),
        "csrf_token": context.get("csrf_token", None),
    }))


@register.simple_tag(takes_context=True)
def bootstrap_create_modal(context, form, action, *args):
    return mark_safe(render_to_string("bootstrap_form/modal_create.html", {
        "form": form,
        "action": reverse(action, args=args),
        "csrf_token": context.get("csrf_token", None),
    }))


@register.simple_tag(takes_context=True)
def bootstrap_confirm_modal(context, name, body, action, *args):
    return mark_safe(render_to_string("bootstrap_form/modal_confirm.html", {
        "name": name,
        "body": body,
        "action": reverse(action, args=args),
        "csrf_token": context.get("csrf_token", None),
    }))


@register.simple_tag(takes_context=True)
def bootstrap_form_modal(context, id, title, form, action, *args):
    return mark_safe(render_to_string("bootstrap_form/modal_form.html", {
        "id": id,
        "title": title,
        "form": form,
        "action": reverse(action, args=args),
        "csrf_token": context.get("csrf_token", None)
    }))
