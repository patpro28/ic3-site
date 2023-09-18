from django.forms import ModelForm
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from backend.widgets.martor import AdminMartorWidget

class OrganizationForm(ModelForm):
    class Meta:
        widgets = {
            'about': AdminMartorWidget(attrs={'data-markdownfy-url': reverse_lazy('self_preview')})
        }

class OrganizationAdmin(VersionAdmin):
    form = OrganizationForm
    fieldsets = (
        (None, {
            "fields": (
                'name', 'slug', 'short_name'
            ),
        }),
        (_('Organization info'), {
            'fields': (
                'about', 'logo', 'creation_date'
            ),
        }),
        (_('Permission'), {
            'fields': (
                'admins', 'is_open', 'slots', 'access_code'
            ),
        }),
    )
    readonly_fields = ('creation_date',)
    list_display = ('name', 'creation_date')
    ordering = ('name',)
    search_fields = ('name',)
    actions_on_top = True
    actions_on_bottom = True
    