from django import template

register = template.Library()


@register.filter
def verbose_name(thing):
    return thing._meta.verbose_name


@register.filter
def class_name(thing):
    return type(thing).__name__
