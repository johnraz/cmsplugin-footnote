# coding: utf-8
from django.core.cache import cache
from django.db.models import Model

from cms.models.pagemodel import Page
from cms.models.pluginmodel import CMSPlugin
from cms.utils.plugins import downcast_plugins, get_plugins_for_page

from djangocms_text_ckeditor.models import Text
from djangocms_text_ckeditor.utils import plugin_tags_to_id_list

from .models import Footnote
from .settings import CMSPLUGIN_FOOTNOTE_DEBUG


def get_cache_key(obj, placeholder_plugins):
    return 'footnote_plugins__%d_%d' \
            % (obj.pk, placeholder_plugins.filter(plugin_type='FootnotePlugin').count())


def delete_cache_key(page):
    plugins = CMSPlugin.objects.all()
    cache_key = get_cache_key(page, plugins)
    cache.delete(cache_key)


def plugin_is_footnote(plugin):
    return plugin.plugin_type == 'FootnotePlugin'


def plugin_iterator_from_text_plugin(text_plugin):
    try:
        plugin_pk_list = plugin_tags_to_id_list(text_plugin.text.body)
        for pk in plugin_pk_list:
            try:
                yield CMSPlugin.objects.get(pk=pk)
            except CMSPlugin.DoesNotExist, e:
                if CMSPLUGIN_FOOTNOTE_DEBUG:
                    raise e
    except Text.DoesNotExist as e:
        # Deal with empty text_plugin case.
        pass


def get_footnotes_for_object(request, instance=None):
    '''
    Gets the Footnote instances for `objects` and `page`, with the correct order.
    instance is either a placeholder instance or a page instance.
    '''

    if isinstance(instance, Page):
        plugins = get_plugins_for_page(request, instance)
        cache_key = get_cache_key(instance, plugins)
    elif isinstance(instance.page, Page):
        plugins = get_plugins_for_page(request, instance.page)
        cache_key = get_cache_key(instance.page, plugins)
    elif isinstance(instance, Model):
        plugins = instance.get_plugins()
        cache_key = get_cache_key(instance, plugins)
    else:
        raise ValueError('Instance must either be a placeholder or a page instance!')

    footnote_ids = cache.get(cache_key)

    if footnote_ids is None:
        root_footnote_and_text_plugins = plugins.filter(
                plugin_type__in=('FootnotePlugin', 'TextPlugin'),
                parent=None
            ).order_by('position')
        footnote_plugins = []
        footnote_plugins__append = footnote_plugins.append
        for p in root_footnote_and_text_plugins:
            if plugin_is_footnote(p):
                footnote_plugins__append(p)
            else:
                try:
                    text = downcast_plugins((p,))[0]
                except IndexError:
                    continue
                plugin_iterator = plugin_iterator_from_text_plugin(text)
                for plugin in plugin_iterator:
                    if plugin_is_footnote(plugin):
                        footnote_plugins__append(plugin)
        footnote_ids = tuple(f.pk for f in downcast_plugins(footnote_plugins))
        cache.set(cache_key, footnote_ids)
    return Footnote.objects.filter(pk__in=footnote_ids)
