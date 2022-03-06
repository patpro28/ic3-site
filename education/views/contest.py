from collections import namedtuple
from operator import attrgetter
from django import forms
from django.db import IntegrityError
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.views.generic.detail import BaseDetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.functional import cached_property
from django.db.models import Q, F, Max

from backend.utils.views import generic_message, QueryStringSortMixin, TitleMixin
from education.models import Contest
from education.models.contest import ContestParticipation

class ContestMixin(object):
  context_object_name = 'contest'
  slug_field = 'key'
  slug_url_kwarg = 'contest'
  model = Contest

  def get_object(self, queryset=None):
    contest = super().get_object(queryset)
    user = self.request.user
    if user is not None and ContestParticipation.objects.filter(id=user.current_contest_id, contest_id=contest.id).exists():
      return contest
    if not contest.is_accessible_by(user):
      raise Http404
    return contest

  def no_such_contest(self):
    key = self.kwargs.get(self.slug_url_kwarg, None)
    return generic_message(self.request, _('No such contest'),
                          _('Could not find a contest with the key "%s".') % key, status=404)

  @cached_property
  def is_editor(self):
    if not self.request.user.is_authenticated:
      return False
    return self.request.user.id in self.object.editor_ids

  @cached_property
  def is_curators(self):
    if not self.request.user.is_authenticated:
      return False
    return self.request.user.id in self.object.curator_ids

  @cached_property
  def can_edit(self):
    return self.object.is_editable_by(self.request.user)

  def get_context_data(self, **kwargs):
      context = super().get_context_data(**kwargs)
      context["now"] = timezone.now()
      context['is_editor'] = self.is_editor
      context['is_curators'] = self.is_curators
      context['can_edit'] = self.can_edit

      if self.request.user.is_authenticated:
        try:
          context['live_participation'] = (
            self.request.user.contest_history.get(
              contest=self.object,
              virtual=ContestParticipation.LIVE
            )
          )
        except ContestParticipation.DoesNotExist:
          context['live_participation'] = None
          context['has_joined'] = False
        else:
          context['has_joined'] = True
      else:
        context['live_participation'] = None
        context['has_joined'] = False
      context['logo_override_image'] = self.object.logo_override_image
      if not context['logo_override_image'] and self.object.organizations.count() == 1:
        context['logo_override_image'] = self.object.organizations.first().logo_override_image
      
      return context
  

  def get(self, request, *args, **kwargs):
    try:
      return super().get(request, *args, **kwargs)
    except Http404:
      return self.no_such_contest()


class ContestListMixin(object):
  def get_queryset(self):
    return Contest.get_visible_contests(self.request.user)


class ContestList(QueryStringSortMixin, TitleMixin, ListView):
  model = Contest
  template_name = ''
  title = _('Contests')
  context_object_name = 'contests'
  paginate_by = 20
  all_sort = frozenset(('name', 'user_count', 'start_time'))
  default_desc = frozenset(('name', 'user_count'))
  default_sort = '-start_time'

  @cached_property
  def _now(self):
    return timezone.now()
  
  def _get_queryset(self):
    return super().get_queryset().prefetch_related('organizations', 'authors', 'curators')

  def get_queryset(self):
    return self._get_queryset().filter(end_time__lt=self._now).order_by(self.order, 'key')
    
  def get_context_data(self, **kwargs):
      context = super().get_context_data(**kwargs)
      present, active, future = [], [], []
      for contest in self._get_queryset().exclude(end_time__lt=self._now):
        if contest.start_time > self._now:
          future.append(contest)
        else:
          present.append(contest)
      
      if self.request.user.is_authenticated:
        for participation in ContestParticipation.objects.filter(virtual=0, user=self.request.user, contest_id__in=present) \
                              .select_related('contest') \
                              .prefetch_related('contest__authors', 'contest__curators') \
                              .annotate(key=F('contest__key')):
          if not participation.ended:
            active.append(participation)
            present.remove(participation.contest)
      
      active.sort(key=attrgetter('end_time', 'key'))
      present.sort(key=attrgetter('end_time', 'key'))
      future.sort(key=attrgetter('start_time'))

      context['active_participations'] = active
      context['current_contests'] = present
      context['future_contests'] = future
      context['now'] = self._now
      context['first_page_href'] = '.'
      context['page_suffix'] = '#past-contests'
      context.update(self.get_sort_context())
      context.update(self.get_sort_paginate_context())
      return context
  

class ContestDetail(ContestMixin, TitleMixin, DetailView):
  template_name = ''

  def get_title(self):
    return self.object.name
  

class ContestAccessDenied(Exception):
  pass


class ContestAccessForm(forms.Form):
  access_code = forms.CharField(max_length=255)

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.field['access_code'].widget.attrs.update({'autocomplete': 'off'})

class ContestJoin(LoginRequiredMixin, ContestMixin, BaseDetailView):
  def get(self, request, *args, **kwargs):
    self.object = self.get_object()
    return self.ask_for_access_code()

  def post(self, request, *args, **kwargs):
    self.object = self.get_object()
    try:
      return self.join_contest(request)
    except ContestAccessDenied:
      if request.POST.get('access_code'):
        return self.ask_for_access_code(ContestAccessForm(request.POST))
      else:
        return HttpResponseRedirect(request.path)
  
  def join_contest(self, request, access_code=None):
    contest = self.object

    if not contest.can_join and not self.is_editor:
      return generic_message(request, _('Contest not ongoing'),
                            _('"%s" is not currently ongoing.') % contest.name)
    
    user = request.user
    if user.current_contest is not None:
      return generic_message(request, _('Already in contest'),
                            _('You are already in a contest "%s".') % user.current_contest.contest.name)
    
    if not user.is_superuser and contest.banned_users.filter(id=user.id).exists():
      return generic_message(request, _('Banned from joining'),
                            _('You have been declared persona non grata for this contest. '
                              'You are permanently barred from joining this contest.'))
    
    required_access_code = (not self.can_edit and contest.access_code and access_code != contest.access_code)

    if contest.ended:
      if required_access_code:
        raise ContestAccessDenied()
      
      while True:
        virtual_id = max((ContestParticipation.objects.filter(contest=contest, user=user)
                          .aggregate(virtual_id=Max('virtual'))['virtual_id'] or 0) + 1, 1)
        try:
          participation = ContestParticipation.objects.create(
            contest=contest,
            user=user,
            virtual=virtual_id,
            real_start=timezone.now()
          )
        except IntegrityError:
          pass
        else:
          break
    else:
      SPECTATE = ContestParticipation.SPECTATE
      LIVE = ContestParticipation.LIVE

      try:
        participation = ContestParticipation.objects.get(
          contest=contest, user=user, virtual=(SPECTATE if self.is_editor else LIVE)
        )
      except ContestParticipation.DoesNotExist:
        if required_access_code:
          raise ContestAccessDenied()
        
        participation = ContestParticipation.objects.create(
          contest=contest,
          user=user,
          virtual=(SPECTATE if self.is_editor else LIVE),
          real_start=timezone.now()
        )
      else:
        if participation.ended:
          participation = ContestParticipation.objects.get_or_create(
            contest=contest,
            user=user,
            virtual=SPECTATE,
            defaults={'real_start': timezone.now()}
          )[0]
    
    user.current_contest = participation
    user.save()
    contest._updating_stats_only = True
    contest.update_user_count()
    return HttpResponseRedirect(reverse('education:contest_detail'))
  
  def ask_for_access_code(self, form=None):
    contest = self.object
    wrong_code = False
    if form:
      if form.is_valid():
        if form.cleaned_data['access_code'] == contest.access_code:
          return self.join_contest(self.request, form.cleaned_data['access_code'])
        wrong_code = True
    else:
      form = ContestAccessForm()
    return render(self.request, 'contest/access_code.html', {
      'form': form,
      'wrong_code': wrong_code,
      'title': _('Enter access code for "%s"') % contest.name
    })


class ContestLeave(LoginRequiredMixin, ContestMixin, BaseDetailView):
  def post(self, request, *args, **kwargs):
    contest = self.get_object()
    user = request.user
    if user.current_contest is None or user.current_contest.contest_id != contest.id:
      return generic_message(request, _('No such contest'),
                            _('You are not in contest "%s".') % contest.key, status=404)
    
    user.remove_contest()
    return HttpResponseRedirect(reverse('contest_view', args=(contest.key,)))


ContestRankingProfile = namedtuple(
  'ContestRankingProfile',
  'id user css_class username points cumtime tiebreaker organization participation '
  'participation_rating problem_cells result_cell',
)

BestSolutionData = namedtuple(
  'BestSolutionData', 'code points time state is_pretested'
)

def make_contest_ranking_profile(contest, participation, contest_problems):
  def display_user_problem(contest_problem):
    try:
      return contest.format.display_user_problem(participation, contest_problem)
    except (KeyError, TypeError, ValueError):
      return mark_safe('<td>???</td>')

  user = participation.user

  return ContestRankingProfile(
    id=user.id,
    user=user,
    css_class=user.css_class,
    username=user.username,
    points=participation.score,
    cumtime=participation.cumtime,
    tiebreaker=participation.tiebreak,
    organization=user.organization,
    participation_rating=participation.rating.rating if hasattr(participation, 'rating') else None,
    problem_cells=[display_user_problem(problem) for problem in contest_problems],
    result_cell=contest.format.display_participation_result(participation),
    participation=participation
  )

def base_contest_ranking_list(contest, problems, queryset):
  return [make_contest_ranking_profile(contest, participation, problems) for participation in 
          queryset.select_related('user', 'rating').defer('user__about', 'user__organization__about')]

def contest_ranking_list(contest, problems):
  return base_contest_ranking_list(contest, problems, contest.users.filter(virtual=0)
                                  .prefetch_related('user__organizations')
                                  .order_by('is_disqualified', '-score', 'cumtime', 'tiebreaker'))