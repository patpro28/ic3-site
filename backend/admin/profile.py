from django.forms import HiddenInput, ModelForm, PasswordInput, CharField
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils.translation import gettext, gettext_lazy as _
from django.urls import reverse, reverse_lazy
from django.db import models

from reversion.admin import VersionAdmin
from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from django.contrib.auth.hashers import make_password
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from backend.widgets.martor import AdminMartorWidget

from backend.models import Profile


class ProfileForm(ModelForm):
    class Meta:
        widgets = {
            'about': AdminMartorWidget(attrs={'data-markdownfy-url': reverse_lazy('self_preview')}),
        }


# class ProfileAddForm(ModelForm):
#     password1 = CharField(label=_('Password'), widget=PasswordInput)
#     password2 = CharField(label=_('Password confirmation'), widget=PasswordInput)

#     class Meta:
#         model = Profile
#         fields = ('username', 'fullname')
    
#     def clean_password2(self):
#         password1 = self.cleaned_data.get('password1')
#         password2 = self.cleaned_data.get('password2')
#         if password1 and password2 and password1 != password2:
#             raise ValidationError(_("Passwords don't match"))
#         return password2 
    
#     def save(self, commit=False):
#         profile = super().save(commit=False)
#         profile.set_password(self.cleaned_data['password1'])
#         if commit:
#             profile.save()
#         return profile


class TimezoneFilter(admin.SimpleListFilter):
    title = _('timezone')
    parameter_name = 'timezone'

    def lookups(self, request, model_admin):
        return Profile.objects.values_list('timezone', 'timezone').distinct().order_by('timezone')

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(timezone=self.value())


class ProfileAdmin(admin.ModelAdmin):
    form = ProfileForm
    fieldsets = (
        (None, {
            "fields": (
                'user', 'display_rank',
            ),
        }),
        (_('Personal info'), {
            "fields": (
                'about','organizations', 'timezone',
            ),
        })
    )
    
    readonly_fields = ('user', )
    list_display = ('username', 'timezone', 'show_public')
    ordering = ('user__username',)
    list_filter = (TimezoneFilter, )
    actions_on_top = True
    actions_on_bottom = True

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields
        # if obj is not None:
        #     fields += ('username', 'password')
        # if not request.user.is_superuser:
        #     fields += ('is_superuser', 'groups')
        #     if not request.user.is_staff:
        #         fields += ('is_staff',)
        return fields
    
    def get_list_display(self, request):
        # if request.user.is_superuser and 'change_password' not in self.list_display:
        #     self.list_display += ('change_password',)
        # if not request.user.is_superuser and 'change_password' in self.list_display:
        #     self.list_display.remove('change_password')
        return self.list_display

    # def change_password(self, obj):
    #     return format_html('<a class="ui blue button" href="{0}" style="white-space:nowrap;">{1}</a>',
    #                         reverse('admin:auth_user_password_change', kwargs={'id':obj.pk}), gettext('Change password'))

    def show_public(self, obj):
        return format_html('<a class="ui blue button" href="{0}" style="white-space:nowrap;">{1}</a>',
                           obj.get_absolute_url(), gettext('View on site'))
    show_public.short_description = ''
