from django.core.cache import cache
from django.forms.models import ModelChoiceIterator, ModelChoiceField, ModelMultipleChoiceField


class CachingModelChoiceIterator(ModelChoiceIterator):
    def _queryset_key(self):
        return str(self.queryset.model._meta.label) + str(self.queryset.query.where).replace(" ", "")

    def __iter__(self):
        choices = cache.get_or_set(self._queryset_key(),
                                   lambda: list(super(CachingModelChoiceIterator, self).__iter__()),
                                   2)
        yield from iter(choices)

    def __len__(self):
        return cache.get_or_set("len:" + self._queryset_key(),
                                super(CachingModelChoiceIterator, self).__len__,
                                2)


class CachingModelMultipleChoiceField(ModelMultipleChoiceField):
    iterator = CachingModelChoiceIterator


class CachingModelChoiceField(ModelChoiceField):
    iterator = CachingModelChoiceIterator
