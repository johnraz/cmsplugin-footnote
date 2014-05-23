# coding: utf-8

from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from cms.plugin_pool import plugin_pool
from djangocms_text_ckeditor.cms_plugins import TextPlugin

from .models import Footnote
from .utils import get_footnotes_for_object
from .utils import delete_cache_key


class FootnotePlugin(TextPlugin):
    model = Footnote
    name = _('Footnote')
    render_template = 'cmsplugin_footnote/footnote_symbol.html'
    text_enabled = True
    admin_preview = False

    def get_editor_widget(self, request, plugins, pk,  placeholder, language):
        plugins.remove(FootnotePlugin)
        return super(FootnotePlugin, self).get_editor_widget(request, plugins, pk, placeholder, language)

    def icon_src(self, instance):
        return settings.STATIC_URL + 'icons/footnote_symbol.png'

    def render(self, context, instance, placeholder_name):
        context = super(FootnotePlugin, self).render(context, instance,
                                                     placeholder_name)

        request = context['request']

        footnotes = list(get_footnotes_for_object(request, instance.placeholder))
        context['counter'] = footnotes.index(instance) + 1
        return context

    def save_model(self, request, obj, form, change):
        super(FootnotePlugin, self).save_model(request, obj, form, change)

        delete_cache_key(self.placeholder._get_attached_objects()[0] if self.placeholder.page_id is None
                            else self.placeholder.page)


plugin_pool.register_plugin(FootnotePlugin)
