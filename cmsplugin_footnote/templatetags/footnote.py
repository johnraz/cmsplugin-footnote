# coding: utf-8
from django.db import models
from django.template import Library

from cms.models.fields import PlaceholderField
from cms.models.pagemodel import Page

from ..models import Footnote
from ..utils import get_footnotes_for_object

register = Library()


@register.inclusion_tag('cmsplugin_footnote/footnote_list.html',
                        takes_context=True)
def footnote_list(context, obj=None):
    """
    obj is a model instance that should be checked upon any placeholder field
    """
    request = context['request']
    footnotes = Footnote.objects.none()
    if obj is None:
        obj = request.current_page

    if isinstance(obj, Page):
        footnotes = get_footnotes_for_object(request, obj)

    elif isinstance(obj, models.Model):
        for field in obj._meta.fields:
            if isinstance(field, PlaceholderField) and getattr(obj, field.name):
                footnotes |= get_footnotes_for_object(request, getattr(obj, field.name))

    context['footnotes'] = footnotes
    return context
