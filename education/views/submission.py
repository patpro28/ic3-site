from collections import defaultdict

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist, PermissionDenied
from django.urls import reverse
from django.utils.html import format_html, escape
from django.utils import timezone
from django.utils.functional import cached_property
from django.db.models import Q, Count
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from backend.models.profile import Profile

from backend.utils.infinite_paginator import InfinitePaginationMixin
from backend.utils.problems import _get_result_data
from backend.utils.raw_sql import join_sql_subquery, use_straight_join
from backend.utils.views import DiggPaginatorMixin, TitleMixin

from education.models import Submission, Contest
from education.models.submission import SubmissionProblem

class SubmissionMixin(object):
    model = Submission
    context_object_name = 'submission'
    pk_url_kwarg = 'pk'


def filter_submissions_by_visible_contests(queryset, user):
    join_sql_subquery(
        queryset,
        subquery=str(Contest.get_visible_contests(user).only('id').query),
        params=[],
        join_fields=[('contest__contest_id', 'id')],
        alias='visible_contests',
    )

def submission_related(queryset):
    return queryset.select_related('user__user', 'contest') \
        .only('id', 'user__user__user__username', 'user__user__display_rank', 'contest__name',
              'contest__key', 'date', 'time',
              'points', 'result', 'contest') \
        .prefetch_related('contest__authors', 'contest__curators')


def get_result_data(*args, **kwargs):
    if args:
        submissions = args[0]
        if kwargs:
            raise ValueError(_("Can't pass both queryset and keyword filters"))
    else:
        submissions = Submission.objects.filter(**kwargs) if kwargs is not None else Submission.objects
    raw = submissions.values('result').annotate(count=Count('result')).values_list('result', 'count')
    return _get_result_data(defaultdict(int, raw))


class SubmissionsListBase(DiggPaginatorMixin, TitleMixin, ListView):
    model = Submission
    paginate_by = 50
    show_problem = True
    title = _('All submissions')
    content_title = _('All submissions')
    tab = 'all_submissions_list'
    template_name = 'submission/list.html'
    context_object_name = 'submissions'
    first_page_href = None

    def get_result_data(self):
        return self._get_result_data()

    def _get_result_data(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_result_data(queryset.order_by())

    @cached_property
    def in_contest(self):
        return self.request.user.is_authenticated and self.request.user.profile.current_contest is not None
    
    @cached_property
    def contest(self):
        return self.request.profile.current_contest.contest

    def _get_queryset(self):
        queryset = Submission.objects.all()
        use_straight_join(queryset)
        queryset = submission_related(queryset.order_by('-id'))
        if self.in_contest:
            queryset = queryset.filter(contest=self.contest)
            if not self.contest.can_see_full_scoreboard(self.request.user):
                queryset = queryset.filter(user__user=self.request.user)
        elif self.request.user.is_authenticated:
            if not self.request.user.has_perm('education.see_private_contest'):
                contest_queryset = Contest.objects.filter(Q(authors=self.request.user) |
                                                          Q(curators=self.request.user) |
                                                          Q(scoreboard_visibility=Contest.SCOREBOARD_VISIBLE) |
                                                          Q(end_time__lt=timezone.now())).distinct()
                queryset = queryset.filter(Q(user__user=self.request.profile) |
                                           Q(contest__in=contest_queryset) |
                                           Q(contest__isnull=True))
        return queryset
    
    def get_queryset(self):
        queryset = self._get_queryset()
        return queryset

    def get_context_data(self, **kwargs):
        context = super(SubmissionsListBase, self).get_context_data(**kwargs)
        # authenticated = self.request.user.is_authenticated
        context['dynamic_update'] = False
        context['dynamic_contest_id'] = self.in_contest and self.contest.id
        context['show_problem'] = self.show_problem

        # context['results_json'] = mark_safe(json.dumps(self.get_result_data()))
        # context['results_colors_json'] = mark_safe(json.dumps(settings.DMOJ_STATS_SUBMISSION_RESULT_COLORS))

        context['page_suffix'] = suffix = ('?' + self.request.GET.urlencode()) if self.request.GET else ''
        context['first_page_href'] = (self.first_page_href or '.') + suffix
        # context['my_submissions_link'] = self.get_my_submissions_page()
        # context['all_submissions_link'] = self.get_all_submissions_page()
        context['tab'] = self.tab
        return context

    
class AllSubmissions(InfinitePaginationMixin, SubmissionsListBase):
    stats_update_interval = 3600

    @property
    def use_infinite_pagination(self):
        return True

    def get_queryset(self):
        return super().get_queryset().exclude(result='PE')

    def get_context_data(self, **kwargs):
        context = super(AllSubmissions, self).get_context_data(**kwargs)
        context['dynamic_update'] = context['page_obj'].number == 1
        # context['last_msg'] = event.last()
        context['stats_update_interval'] = self.stats_update_interval
        return context


class ContestSubmissionsBase(SubmissionsListBase):
    show_problem = False
    dynamic_update = False

    def get_queryset(self):
        # if self.in_contest and not self.contest.contest_problems.filter(problem_id=self.problem.id).exists():
        #     raise Http404()
        return super()._get_queryset().filter(contest__contest_id=self.contest.id)

    def get_title(self):
        return _('All submissions for %s') % self.contest_name

    def get_content_title(self):
        return format_html('All submissions for <a href="{1}">{0}</a>', self.contest_name,
                           reverse('education:contest_detail', args=[self.contest.key]))

    def access_check_contest(self, request):
        if self.in_contest and not self.contest.can_see_own_scoreboard(request.user):
            raise Http404()

    def access_check(self, request):
        # FIXME: This should be rolled into the `is_accessible_by` check when implementing #1509
        if self.in_contest and request.user.is_authenticated and request.user.id in self.contest.editor_ids:
            return

        if not self.contest.is_accessible_by(request.user):
            raise Http404()

        # if self.check_contest_in_access_check:
        #     self.access_check_contest(request)

    def get(self, request, *args, **kwargs):
        if 'contest' not in kwargs:
            raise ImproperlyConfigured(_('Must pass a contest'))
        self.contest = get_object_or_404(Contest, key=kwargs['contest'])
        self.contest_name = self.contest.name
        return super().get(request, *args, **kwargs)

    def get_all_submissions_page(self):
        return reverse('education:all_submissions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['best_submissions_link'] = reverse('ranked_submissions', kwargs={'problem': self.contest.key})
        return context


class ContestSubmissions(ContestSubmissionsBase):
    def get_my_submissions_page(self):
        if self.request.user.is_authenticated:
            return reverse('education:user_submission', kwargs={
                'contest': self.contest.key,
                'user': self.request.user.username,
            })


class UserMixin(object):
    def get(self, request, *args, **kwargs):
        if 'user' not in kwargs:
            raise ImproperlyConfigured('Must pass a user')
        self.profile = get_object_or_404(Profile, user__username=kwargs['user'])
        self.username = kwargs['user']
        return super(UserMixin, self).get(request, *args, **kwargs)


class ConditionalUserTabMixin(object):
    @cached_property
    def is_own(self):
        return self.request.user.is_authenticated and self.request.user == self.profile
    
    def get_context_data(self, **kwargs):
        context = super(ConditionalUserTabMixin, self).get_context_data(**kwargs)
        if self.is_own:
            context["tab"] = 'my_submissions_tab'
        else:
            context['tab'] = 'user_submissions_tab'
            context['tab_user'] = self.profile.username
        return context
    

class AllUserSubmissions(ConditionalUserTabMixin, UserMixin, SubmissionsListBase):
    def get_queryset(self):
        return super(AllUserSubmissions, self).get_queryset().filter(user_id=self.profile.id)

    def get_title(self):
        if self.is_own:
            return _('All my submissions')
        return _('All submissions by %s') % self.username

    def get_content_title(self):
        if self.is_own:
            return format_html('All my submissions')
        return format_html('All submissions by <a href="{1}">{0}</a>', self.username,
                           reverse('user_page', args=[self.username]))

    def get_my_submissions_page(self):
        if self.request.user.is_authenticated:
            return reverse('all_user_submissions', kwargs={'user': self.request.user.username})

    def get_context_data(self, **kwargs):
        context = super(AllUserSubmissions, self).get_context_data(**kwargs)
        context['dynamic_update'] = context['page_obj'].number == 1
        context['dynamic_user_id'] = self.profile.id
        # context['last_msg'] = event.last()
        return context


class UserContestSubmissions(ConditionalUserTabMixin, UserMixin, ContestSubmissions):
    
    def access_check(self, request):
        super().access_check(request)

        if not self.is_own:
            self.access_check_contest(request)

    def get_queryset(self):
        return super().get_queryset().filter(user_id=self.profile.id)

    def get_title(self):
        if self.is_own:
            return _("My submissions for %(contest)s") % {'contest': self.contest_name}
        return _("%(user)s's submissions for %(contest)s") % {'user': self.username, 'contest': self.contest_name}

    def get_content_title(self):
        if self.request.user.is_authenticated and self.request.user == self.profile:
            return format_html('''My submissions for <a href="{3}">{2}</a>''',
                               self.username, reverse('user_page', args=[self.username]),
                               self.contest_name, reverse('education:contest_detail', args=[self.contest.key]))
        return format_html('''<a href="{1}">{0}</a>'s submissions for <a href="{3}">{2}</a>''',
                           self.username, reverse('user_page', args=[self.username]),
                           self.contest_name, reverse('education:contest_detail', args=[self.contest.key]))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dynamic_user_id'] = self.profile.id
        return context


class SubmissionDetailBase(LoginRequiredMixin, TitleMixin, SubmissionMixin, DetailView):
    def get_object(self, queryset=None):
        submission = super(SubmissionDetailBase, self).get_object(queryset)
        return submission

    def get_title(self):
        submission = self.object
        return _('Submission of %(contest)s by %(user)s') % {
            'contest': submission.contest.name,
            'user': submission.user.user.username,
        }

    def get_content_title(self):
        submission = self.object
        return mark_safe(escape(_('Submission of %(contest)s by %(user)s')) % {
            'contest': format_html('<a href="{0}">{1}</a>',
                                   reverse('education:contest_detail', kwargs={'contest': submission.contest.key}),
                                   submission.contest.name),
            'user': format_html('<a href="{0}">{1}</a>',
                                reverse('user_page', kwargs={'user': submission.user.user.username}),
                                submission.user.user.username),
        })


class SubmissionStatus(SubmissionDetailBase):
    template_name = 'submission/status.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submission = self.object
        problems = submission.contest.contest_problems.all().order_by('order')
        context['status'] = []
        context['pending'] = context['correct'] = context['wrong'] = 0
        for problem in problems:
            try:
                sp = SubmissionProblem.objects.get(
                    submission=submission,
                    problem=problem
                )
            except SubmissionProblem.DoesNotExist:
                sp = None
            if sp is None:
                context['status'].append((None, '------'))
                context['pending'] += problem.points
            else:
                context['status'].append((sp.output, sp.get_long_status))
                if sp.result:
                    context['correct'] += problem.points
                else:
                    context['wrong'] += problem.points
        context['point'] = submission.points * 100 / submission.max_points
        return context
    