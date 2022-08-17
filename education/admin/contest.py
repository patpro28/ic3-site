import os
from django.urls import reverse, reverse_lazy
from reversion.admin import VersionAdmin
from adminsortable2.admin import SortableInlineAdminMixin

from django import forms
from django.urls import path
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib import admin
from django.conf import settings
from django.db.models import Q
from django.utils.translation import gettext, gettext_lazy as _, ngettext
from django.utils.html import format_html

from semantic_admin import widgets
from semantic_admin.admin import SemanticTabularInline, SemanticModelAdmin, SemanticStackedInline
from backend.models.profile import Profile

from backend.widgets.martor import AdminMartorWidget, MartorWidget

from education.models import ContestProblem
from education.models.contest import Contest, ContestParticipation, ContestSolution

class ContestProblemInline(SemanticTabularInline, SortableInlineAdminMixin):
  model = ContestProblem
  fields = ('problem', 'points', 'order')


class ContestSolutionForm(forms.ModelForm):
  model = ContestSolution

  class Meta:
    widgets = {
      'content': AdminMartorWidget(attrs={'data-markdownfy-url': reverse_lazy('description_preview')})
    }

class ContestSolutionInline(SemanticStackedInline):
  model = ContestSolution
  fields = ('authors', 'is_public', 'publish_on', 'is_full_markup', 'content')
  extra = 0
  max_num = 1
  form = ContestSolutionForm


class ContestAdminForm(forms.ModelForm):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def clean(self):
    cleaned_data = super().clean()
    cleaned_data['banned_users'].filter(current_contest__contest=self.instance).update(current_contest=None)

    return cleaned_data

  class Meta:
    widgets = {
      'authors': widgets.SemanticSelectMultiple,
      'curators': widgets.SemanticSelectMultiple,
      'organizations': widgets.SemanticSelectMultiple,
      'banned_users': widgets.SemanticSelectMultiple,
      'scoreboard_visibility': widgets.SemanticSelect,
      'start_time': widgets.SemanticDateTimeInput,
      'end_time': widgets.SemanticDateTimeInput,
      'private_contestants': widgets.SemanticSelectMultiple,
      'view_contest_scoreboard': widgets.SemanticSelectMultiple,
      'description': AdminMartorWidget(attrs={'data-markdownfy-url': reverse_lazy('description_preview')})
    }


class ContestAdmin(SemanticModelAdmin):
  form = ContestAdminForm
  fieldsets = (
      (None, {
        "fields": (
          'key', 'name', 'authors', 'curators'
        ),
      }),
      (_('Access'), {
        'fields': (
          'access_code', 'is_private', 'private_contestants', 'is_organization_private',
          'organizations', 'view_contest_scoreboard', 'banned_users'
        ),
      }),
      (_('Settings'), {
        "fields": (
          'is_visible', 'scoreboard_visibility', 'points_precision'
        ),
      }),
      (_('Details'), {'fields': ('description', 'og_image', 'logo_override_image', 'summary')}),
      (_('Scheduling'), {'fields': ('start_time', 'end_time', )}),
  )
  list_display = ['key', 'name', 'is_visible', 'show_public', 'show_word']
  inlines = [ContestProblemInline, ContestSolutionInline]
  ordering = ('key',)
  search_fields = ('key', 'name',)
  date_hierarchy = 'start_time'
  actions_on_top = True
  actions_on_bottom = True

  def get_actions(self, request):
      actions = super().get_actions(request)
      if request.user.has_perm('education.change_contest_visibility') or \
          request.user.has_perm('education.create_private_contest'):
        for action in ('make_visible', 'make_hidden'):
            actions[action] = self.get_action(action)
      return actions

  def make_visible(self, request, queryset):
    if not request.user.has_perm('education.change_contest_visibility'):
        queryset = queryset.filter(Q(is_private=True) | Q(is_organization_private=True))
    count = queryset.update(is_visible=True)
    self.message_user(request, ngettext('%d contest successfully marked as visible.',
                                        '%d contests successfully marked as visible.',
                                        count) % count)
  make_visible.short_description = _('Mark contests as visible')

  def make_hidden(self, request, queryset):
    if not request.user.has_perm('education.change_contest_visibility'):
        queryset = queryset.filter(Q(is_private=True) | Q(is_organization_private=True))
    count = queryset.update(is_visible=True)
    self.message_user(request, ngettext('%d contest successfully marked as hidden.',
                                        '%d contests successfully marked as hidden.',
                                        count) % count)
  make_hidden.short_description = _('Mark contests as hidden')

  def get_form(self, request, obj=None, **kwargs):
    form = super().get_form(request, obj, **kwargs)

    perms = ('edit_own_contest', 'edit_all_contest')
    form.base_fields['curators'].queryset = Profile.objects.filter(
      Q(is_superuser=True) |
      Q(groups__permissions__codename__in=perms) |
      Q(user_permissions__codename__in=perms)
    ).distinct()
    return form

  def get_urls(self):
    return [
      path('<int:id>/word/', self.export_word, name="contest_word"),
    ] + super().get_urls()

  def export_word(self, request, id):
    from education.signals import unlink_if_exists
    from education.views.contest import get_answer_contest_problem
    import pandoc
    import io

    contest = get_object_or_404(Contest, id=id)
    problems = [e.problem for e in ContestProblem.objects.select_related('problem').filter(contest=contest)]
    file = os.path.join(settings.WORD_CONTEST_CACHE, "contest_{}.docx".format(contest.key))
    if os.path.exists(file):
      unlink_if_exists(file)
    md = "# {}\r\n\r\n".format(contest.name)
    for index, problem in enumerate(problems):
      md += "**Problem %s**: " % (index + 1) + str(problem.description) + "\r\n\r\n"
      if problem.answer_type == 'mc':
        answers = get_answer_contest_problem(problem)
        max_length = 0
        for index, item in answers:
          max_length = max(max_length, len(item))
        if max_length > 30:
          for index, item in answers:
            md += '\t' + index + ". " + item + "\r\n"
        else:
          md += "+----------------------------------+-----------------------------------+\r\n"
          i = 0
          for index, item in answers:
            i += 1
            s = " **%s**. %s" % (index, item)
            while len(s) < 34:
              s += ' '
            md += '\x7c' + s
            if i % 2 == 0:
              md += "\x7c\r\n+----------------------------------+-----------------------------------+\r\n"
          if i % 2 == 1:
            md += "\x7c\r\n+----------------------------------+-----------------------------------+\r\n"
      md += "\r\n"
      
    md = md.replace('~', '$')
    md = md.replace('](/', '](%s/' % settings.SITE_FULL_URL)
    doc = pandoc.read(source=md, format='markdown')
    pandoc.write(doc=doc, format='docx', file=file)
    # pandoc.write(doc=doc, format='markdown', file="/tmp/%s.md" % (contest.key))
    f = io.open(file, mode='rb')
    response = HttpResponse(
      f.read(),
      content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )
    response['Content-Disposition'] = 'attachment; filename="contest_%s.docx"' % (contest.key)
    return response

  def show_public(self, obj):
    return format_html('<a class="ui blue button" href="{0}" style="white-space:nowrap;">{1}</a>',
                        obj.get_absolute_url(), gettext('View on site'))
  def show_word(self, obj):
    return format_html('<a class="ui blue button" href="{0}" style="white-space:nowrap;">{1}</a>',
                        reverse('admin:contest_word', kwargs={'id': obj.id,}), gettext('Export word'))


class ContestParticipationAdmin(SemanticModelAdmin):
    fields = ('contest', 'user', 'real_start', 'virtual', 'is_disqualified')
    list_display = ('contest', 'username', 'show_virtual', 'real_start', 'score', 'cumtime', 'tiebreaker')
    actions = ['recalculate_results']
    actions_on_bottom = actions_on_top = True
    search_fields = ('contest__key', 'contest__name', 'user__username')
    date_hierarchy = 'real_start'

    def get_queryset(self, request):
        return super(ContestParticipationAdmin, self).get_queryset(request).only(
            'contest__name',
            'user__username', 'real_start', 'score', 'cumtime', 'tiebreaker', 'virtual',
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if form.changed_data and 'is_disqualified' in form.changed_data:
            obj.set_disqualified(obj.is_disqualified)

    def recalculate_results(self, request, queryset):
        count = 0
        for participation in queryset:
            participation.recompute_results()
            count += 1
        self.message_user(request, ngettext('%d participation recalculated.',
                                             '%d participations recalculated.',
                                             count) % count)
    recalculate_results.short_description = _('Recalculate results')

    def username(self, obj):
        return obj.user.username
    username.short_description = _('username')
    username.admin_order_field = 'user__user__username'

    def show_virtual(self, obj):
        return obj.virtual or '-'
    show_virtual.short_description = _('virtual')
    show_virtual.admin_order_field = 'virtual'
