from django.forms import ModelForm
from reversion.admin import VersionAdmin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from semantic_admin.widgets import SemanticSelect
from backend.widgets.martor import AdminMartorWidget

class BlogPostForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(BlogPostForm, self).__init__(*args, **kwargs)
        if 'authors' in self.fields:
            # self.fields['authors'] does not exist when the user has only view permission on the model.
            self.fields['authors'].widget.can_add_related = False

    class Meta:
        widgets = {
            'author': SemanticSelect(),
            'description': AdminMartorWidget(attrs={'data-markdownfy-url': reverse_lazy('description_preview')}),
        }


class BlogPostAdmin(VersionAdmin):
    fieldsets = (
        (None, {'fields': ('title', 'author', 'visible', 'publish')}),
        (_('Content'), {'fields': ('description',)}),
    )
    # prepopulated_fields = {'slug': ('title',)}
    list_display = ('id', 'title', 'visible', 'publish')
    list_display_links = ('id', 'title')
    readonly_fields = ('publish', )
    ordering = ('-publish',)
    form = BlogPostForm
    date_hierarchy = 'publish'

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return request.user.has_perm('social.change_blogpost')
        return obj.is_editable_by(request.user)