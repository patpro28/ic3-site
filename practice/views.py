from collections import defaultdict
import random
from django.http import Http404, HttpResponseRedirect

from django.db.models import Count, F, Q
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from backend.utils.infinite_paginator import InfinitePaginationMixin
from backend.utils.problems import _get_result_data
from backend.utils.raw_sql import join_sql_subquery, use_straight_join

from education.models.problem import Level, Problem
from education.views.contest import get_answer_contest_problem
from practice.models.practice import PracticeProblem
from practice.models.submission import SubmissionProblem
from .forms import PracticeForm
from .models import Practice, Submission
from backend.utils.views import DiggPaginatorMixin, TitleMixin, generic_message
from education.models.problem import DIFFICULT

# Create your views here.

FORMAT = (
  ('newbie', 3),
  ('amateur', 2),      
  ('expert', 2),      
  ('cmaster', 1),    
  ('master', 1),   
  ('gmaster', 1),  
  ('target', 0)
)

class PracticeView(TitleMixin, FormView):
  template_name: str = 'practice/practice.html'
  title = 'Practice'
  form_class = PracticeForm

  def form_valid(self, form: PracticeForm):
    level_id = form.cleaned_data['level']
    level = Level.objects.get(id=level_id)
    number = 0
    practice = Practice.objects.create(name='Practice', level=level)
    for difficult, num in reversed(FORMAT):
      number += num
      problems = list(Problem.objects.filter(difficult=difficult, level=level))
      if len(problems) < number:
        number -= len(problems)
        for problem in problems:
          PracticeProblem.objects.create(contest=practice, problem=problem)
      else:
        random.shuffle(problems)
        for problem in problems[:number]:
          PracticeProblem.objects.create(contest=practice, problem=problem)
    return HttpResponseRedirect(reverse('practice:practice_task', kwargs={'pk': practice.id}))


class PracticeTaskView(LoginRequiredMixin, TitleMixin, DetailView):
  template_name = 'practice/tasks.html'
  slug_field: str = 'pk'
  slug_url_kwarg: str = 'pk'
  context_object_name: str = 'contest'
  model = Practice
  
  def get_title(self):
      return "%(contest)s by %(user)s" % {
        'contest': self.object.name,
        'user': self.request.profile.fullname if self.request.profile.fullname else self.request.user.username
      }

  def get_context_data(self, **kwargs):
      context = super().get_context_data(**kwargs)
      problems = list(PracticeProblem.objects.filter(contest=self.object))
      user = self.request.user
      practice = self.object
      context['problems'] = []
      for problem in problems:
        answer = get_answer_contest_problem(problem.problem)
        context['problems'].append((problem, answer))
      if Submission.objects.filter(profile=user, contest=practice).order_by('-date').exists():
        last_submission = Submission.objects.filter(profile=user, contest=practice).order_by('-date').first()
      else:
        last_submission = None
      if last_submission is None or last_submission.result != 'PE':
        submission = Submission.objects.create(
          profile=user,
          contest=practice,
          result='PE'
        )
      else:
        submission = last_submission
      context['submission'] = submission
      return context
  
  def post(self, request, *args, **kwargs):
    id = request.POST.get('contest', None)
    sub_id = request.POST.get('submission', None)
    if id is None or sub_id is None:
      raise Http404
    try:
      practice = Practice.objects.get(id=id)
      submission = Submission.objects.get(id=sub_id)
    except (Practice.DoesNotExist, Submission.DoesNotExist):
      raise Http404

    if submission.problems.exists():
      return generic_message(request, _('Duplicate submission'),
                            _('You must click "Practice" button to start practice'))

    problems = PracticeProblem.objects.filter(contest=practice).select_related('problem').defer('problem__description')
    for problem in problems:
      ans = request.POST.get('answer_' + str(problem.id), None)
      if ans is not None:
        submissionProblem = SubmissionProblem.objects.get_or_create(
          submission=submission,
          problem=problem,
        )[0]
        submissionProblem.output = ans
        submissionProblem.save()
    submission.time = timezone.now()
    # print(submission.id)
    submission.save()
    submission.judge()

    return HttpResponseRedirect(reverse('practice:all_submissions'))
  

class SubmissionMixin(object):
    model = Submission
    context_object_name = 'submission'
    pk_url_kwarg = 'pk'


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
    template_name = 'practice/submission.html'
    context_object_name = 'submissions'
    first_page_href = None

    def get_result_data(self):
        return self._get_result_data()

    def _get_result_data(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_result_data(queryset.order_by())
    
    def get_queryset(self):
        queryset = Submission.objects.all().order_by('-id')
        return queryset

    def get_context_data(self, **kwargs):
        context = super(SubmissionsListBase, self).get_context_data(**kwargs)

        context['page_suffix'] = suffix = ('?' + self.request.GET.urlencode()) if self.request.GET else ''
        context['first_page_href'] = (self.first_page_href or '.') + suffix
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
        return context
