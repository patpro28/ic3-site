from django.urls import reverse_lazy
from reversion.admin import VersionAdmin

from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _, gettext
from django.utils.html import format_html

from semantic_admin.admin import SemanticTabularInline
from semantic_admin import widgets
from martor.widgets import AdminMartorWidget

from education.models import Problem, ProblemGroup, Answer#, Level
from backend.utils.models import AlwaysChangedModelForm



class ProblemGroupAdmin(VersionAdmin):
    fieldsets = (
        (None, {
            "fields": (
                'name', 'short_name'
            ),
        }),
    )
    list_display = ['name',]
    ordering = ('name',)
    actions_on_top = True
    actions_on_bottom = True


class LevelAdmin(VersionAdmin):
    fieldsets = (
        (None, {
            "fields": (
                'code', 'name', 'description'
            ),
        }),
    )
    list_display = ['name',]
    ordering = ('name',)
    actions_on_top = True
    actions_on_bottom = True


class AnswerInlineFormset(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        count = 0
        for form in self.forms:
            count += form.cleaned_data['is_correct'] == True
        if count < 1:
            raise forms.ValidationError('You must have at least one Correct answer')
        if count > 1:
            raise forms.ValidationError('You can only get one correct answer')


class AnswerInline(admin.TabularInline):
    model = Answer
    formset = AnswerInlineFormset
    form = AlwaysChangedModelForm
    fields = ('description', 'is_correct')

    def get_extra(self, request, obj=None, **kwargs):
        extra = 5
        if obj:
            return extra - obj.answers.count()
        return extra


class ProblemForm(forms.ModelForm):
    class Meta:
        widgets = {
            'authors': widgets.SemanticSelectMultiple,
            'description': AdminMartorWidget(attrs={'data-markdownfy-url': reverse_lazy('description_preview')}),
            'organizations': widgets.SemanticSelectMultiple,
            'group': widgets.SemanticSelect
        }


class GroupFilter(admin.SimpleListFilter):
    title = _('group')
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        groups = ProblemGroup.objects.all()
        return [(group.id, group.name) for group in groups]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(group__id=self.value())


class ProblemAdmin(VersionAdmin):
    form = ProblemForm
    fieldsets = (
        (None, {
            "fields": (
                'code', 'name', 'authors', 'is_public', 'is_organization_private', 'organizations'
            ),
        }),
        (_('Description'), {
            'fields': (
                'is_full_markup', 'description', 'difficult', 'group', 'level'
            ),
        })
    )
    
    list_display = ['code', 'name', 'is_public', 'group', 'show_public']
    inlines = [AnswerInline]
    list_filter = (GroupFilter,)
    ordering = ('code',)
    search_fields = ('code', 'name')
    actions_on_top = True
    actions_on_bottom = True

    def show_public(self, obj):
        return format_html('<a class="ui blue button" href="{0}" style="white-space:nowrap;">{1}</a>',
                           obj.get_absolute_url(), gettext('View on site'))