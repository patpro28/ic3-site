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


class ProfileMarkdownPreviewView(MarkdownPreviewView):
    template_name = 'profile/preview.html'