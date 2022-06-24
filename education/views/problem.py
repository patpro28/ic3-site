import json

from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.db.models import Q, Count
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.template.loader import render_to_string
from django.utils import timezone

from backend.utils.diggpaginator import DiggPaginator
from backend.templatetags.markdown import markdown
from education.models import Problem, ProblemGroup
from backend.models import Profile
from backend.utils.views import QueryStringSortMixin, TitleMixin, generic_message
from backend.utils.strings import safe_int_or_none, safe_float_or_none
from education.models.problem import Answer, Level
# from education.models.statistic import StatisticProblem
from education.models.submission import Submission, SubmissionProblem

class ProblemMixin(object):
    context_object_name = 'problem'
    model = Problem
    slug_field = 'code'
    slug_url_kwarg = 'problem'

    def get_object(self, queryset=None):
        problem = super().get_object(queryset)
        if not problem.is_accessible_by(self.request.user):
            raise Http404
        return problem
    
    def no_such_problem(self):
        code = self.kwargs.get(self.slug_url_kwarg, None)
        return generic_message(self.request, _('No such problem'),
                                _('Could not find a problem with the code "%s".') % code, status=404)
    
    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            return self.no_such_problem()


class ProblemListMixin(object):
    def get_queryset(self):
        return Problem.get_visible_problems(self.request.user)


class ProblemList(TitleMixin, ListView):
    model = Problem
    title = _('Problems')
    template_name = 'problem/list.html'
    limit_show = 50

    @cached_property
    def profile(self):
        if not self.request.user.is_authenticated:
            return None
        return self.request.user

    def get_queryset(self):
        filter = Q(is_public=True)
        if self.request.user.is_authenticated:
            filter |= Q(authors=self.profile)
        
        queryset = Problem.objects.filter(filter)
        if not self.request.user.has_perm('education.see_organization_problem'):
            filter = Q(is_organization_private=False)
            if self.profile is not None:
                filter |= Q(organizations__in=self.profile.organizations.all())
            queryset = queryset.filter(filter)
        
        return queryset.distinct()
  

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["category"] = self.category
        levels = Level.objects.all()
        queryset = self.get_queryset()
        context['levels'] = []
        for level in levels:
            problems = queryset.filter(level=level)
            if problems.count() > self.limit_show:
                problems = problems[:self.limit_show - 1]
                has_more = True
            else:
                has_more = False
            context['levels'].append({
                'level'   : level,
                'problems': problems,
                'has_more': has_more
            })
        return context


class ProblemLevelList(QueryStringSortMixin, TitleMixin, ListView):
    model = Level
    context_object_name = 'problems'
    template_name = 'problem/level_list.html'
    paginate_by = 30
    sql_sort = frozenset(('difficult', 'code', 'name'))
    manual_sort = frozenset(('types'))
    all_sorts = sql_sort | manual_sort
    default_desc = frozenset(('-difficult'))
    default_sort = 'code'
    slug_field = 'code'
    slug_url_kwarg = 'level'

    def get_object(self):
        code = self.kwargs.get(self.slug_url_kwarg, None)
        return Level.objects.get(code=code)

    def get_title(self):
        return self.get_object().name

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True, **kwargs):
        paginator = DiggPaginator(queryset, per_page, body=6, padding=2, orphans=orphans, 
                                  allow_empty_first_page=allow_empty_first_page, **kwargs)
        paginator.num_pages
        sort_key = self.order.lstrip('-')
        if sort_key in self.sql_sort:
            queryset = queryset.order_by(self.order, 'id')
        elif sort_key == 'types':
            queryset = queryset.order_by(self.order + '__name', 'id')
        
        paginator.object_list = queryset
        return paginator

    @cached_property
    def user(self):
        if self.request.user.is_authenticated:
            return self.request.user
        return None
    
    def get_queryset(self):
        queryset = Problem.objects.filter(level=self.object)
        filter = Q(is_public=True)
        if self.user is not None:
            filter |= Q(authors=self.user)
        
        queryset = queryset.filter(filter)

        if self.user is None or not self.user.has_perm('education:see_organization_problem'):
            filter = Q(is_organization_private=False)
            if self.user is not None:
                filter |= Q(organizations__in=self.user.organizations.all())
            queryset = queryset.filter(filter)
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update(self.get_sort_paginate_context())
        context.update(self.get_sort_context())
        context['level'] = self.object
        return context

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)
    


def get_answer(problem):
    answers = Answer.objects.filter(problem=problem)
    answer = [(chr(idx + 65), answer.description) for idx, answer in enumerate(answers) ]
    return answer


class ProblemDetail(ProblemMixin, TitleMixin, DetailView):
    context_object_name = 'problem'
    template_name = 'problem/problem.html'

    def get_content_title(self):
        return _('Problem: %s') % self.object.name
    
    def get_title(self):
        return self.object.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # authed = user.is_authenticated
        context['can_edit'] = self.object.is_editable_by(user)
        context['description'] = self.object.description
        context['answers'] = get_answer(self.object)

        return context


def get_types_problem(request):
    level_id = request.GET.get('level', None)
    qs = ProblemGroup.objects.all()
    if level_id:
        qs = qs.filter(problem__level__id=level_id)
    qs = qs.annotate(num_problems=Count('problem')).filter(num_problems__gt=0)
    return JsonResponse({'data': render_to_string('utils/options.html', {'items': qs})})


class ProblemPractice(TitleMixin, TemplateView):
    template_name = 'problem/practice.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["class"] = Level.objects.all()
        context['types'] = get_types_problem(self.request)
        return context
    
    def post(self, request, *args, **kwargs):
        pass

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            return self.post(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)
    

def problemSubmit(request, *args, **kwargs):
    if request.method == 'POST':
        code = kwargs['problem']
        if code is None:
            raise Http404()
        user = request.user
        problem = Problem.objects.get(code=code)
        if Submission.objects.filter(profile=user, problem=problem, time__gt=timezone.now() - timezone.timedelta(seconds=300)).exists():
            submission = Submission.objects.filter(
                profile=user, 
                problem=problem, 
                time__gt=timezone.now() - timezone.timedelta(seconds=300)
            ).first()
            return generic_message(
                request,
                _("Restrict to submit problem"),
                _('You need at least %ss to submit this problem.') % round((submission.time + timezone.timedelta(seconds=300) - timezone.now()).total_seconds()),
            )
        ans = request.POST.get('answer_' + str(problem.id))
        submission = Submission.objects.create(
            profile=user,
            problem=problem, 
            is_contest=False,
            time=timezone.now()
        )
        submissionProblem = SubmissionProblem.objects.get_or_create(
            submission=submission,
            task=problem
        )[0]
        submissionProblem.output = ans
        submissionProblem.save()
        submission.judge()
        # sp = StatisticProblem.objects.get_or_create(user=user, date=timezone.now().date())[0]
        # sp.update_problem(submission)
        return HttpResponseRedirect(reverse('education:all_submissions'))
    else:
        raise Http404()


# def getContent(request, *args, **kwargs):
#     code = kwargs['problem']
#     if code is None:
#         raise Http404()
#     problem = Problem.objects.get(code=code)

#     context = json.dumps({
#         'description': problem.description
#     })

#     return context