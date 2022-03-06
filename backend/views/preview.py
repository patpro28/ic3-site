from django.http import HttpResponseBadRequest
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View


class MarkdownPreviewView(TemplateResponseMixin, ContextMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            self.preview_data = data = request.POST['content']
        except KeyError:
            return HttpResponseBadRequest('No preview data specified.')

        return self.render_to_response(self.get_context_data(
            preview_data=data,
        ))


class DefaultPreviewView(MarkdownPreviewView):
    template_name = 'preview/default.html'


class SelfDescriptionMarkdownPreviewView(MarkdownPreviewView):
    template_name = 'preview/self.html'


class DescriptionMarkdownPreviewView(MarkdownPreviewView):
    template_name = 'preview/description.html'


class DescriptionFullMarkdownPreviewView(MarkdownPreviewView):
    template_name = 'preview/description_full.html'