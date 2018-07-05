from django.core.cache import cache
from django.forms import MultipleChoiceField


class CachingModelMultipleChoiceField(MultipleChoiceField):
    def __init__(self, queryset, *args, **kwargs):
        choices = cache.get(str(queryset))

        if choices is None:
            choices = [(x.pk, str(x)) for x in queryset.all()]
            cache.set(str(queryset), choices, 2)

        super(CachingModelMultipleChoiceField, self).__init__(choices=choices, *args, **kwargs)
