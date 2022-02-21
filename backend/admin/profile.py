from django.forms import ModelForm
from django.utils.html import format_html
from django.utils.translation import gettext, gettext_lazy as _
from django.urls import reverse_lazy
from django.db import models
from reversion.admin import VersionAdmin
from django.contrib import admin

from backend.models import Profile
from martor.widgets import AdminMartorWidget
from martor.models import MartorField

class ProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)

    class Meta:
        widgets = {
            'about': AdminMartorWidget(attrs={'data-markdownfy-url': reverse_lazy('profile_preview')}),
        }


class TimezoneFilter(admin.SimpleListFilter):
    title = _('timezone')
    parameter_name = 'timezone'

    def lookups(self, request, model_admin):
        return Profile.objects.values_list('timezone', 'timezone').distinct().order_by('timezone')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(timezone=self.value())


class ProfileAdmin(VersionAdmin):
    fields = ('username', 'password', 'fullname', 'display_rank', 'about', 'math_engine','organizations', 'timezone', 'last_access')
    readonly_fields = ('username', 'password')
    list_display = ('admin_user_admin', 'timezone_full',
                    'date_joined', 'last_access', 'show_public')
    ordering = ('username',)
    search_fields = ('username',)
    list_filter = (TimezoneFilter, )
    actions = ('recalculate_points',)
    actions_on_top = True
    actions_on_bottom = True
    form = ProfileForm

    def get_queryset(self, request):
        return super(ProfileAdmin, self).get_queryset(request)

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields
        if not request.user.has_perm('judge.totp'):
            fields += ('is_totp_enabled',)
        return fields

    def show_public(self, obj):
        return format_html('<a href="{0}" style="white-space:nowrap;">{1}</a>',
                           obj.get_absolute_url(), gettext('View on site'))
    show_public.short_description = ''

    def admin_user_admin(self, obj):
        return obj.username
    admin_user_admin.admin_order_field = 'username'
    admin_user_admin.short_description = _('User')

    def timezone_full(self, obj):
        return obj.timezone
    timezone_full.admin_order_field = 'timezone'
    timezone_full.short_description = _('Timezone')

    def date_joined(self, obj):
        return obj.date_joined
    date_joined.admin_order_field = 'date_joined'
    date_joined.short_description = _('date joined')

    class Media:
        css = {
            'all': ('lib/bootstrap/css/bootstrap.min.css',),
        }
