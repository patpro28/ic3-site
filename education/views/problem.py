from django.db import ProgrammingError
from django.http import Http404
from django.db.models import Q
from django.views.generic import DetailView, ListView
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from backend.utils.diggpaginator import DiggPaginator

from education.models import Problem, ProblemGroup
from backend.models import Profile
from backend.utils.views import QueryStringSortMixin, TitleMixin, generic_message
from backend.utils.strings import safe_int_or_none, safe_float_or_none
from education.models.problem import Answer

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


class ProblemList(QueryStringSortMixin, TitleMixin, ListView):
    model = Problem
    title = _('Problems')
    context_object_name = 'problems'
    template_name = 'problem/list.html'
    paginate_by = 50
    sql_sort = frozenset(('difficult', 'code', 'name'))
    manual_sort = frozenset(('group'))
    all_sorts = sql_sort | manual_sort
    default_desc = frozenset(('-difficult'))
    default_sort = 'code'

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True, **kwargs):
        paginator = DiggPaginator(queryset, per_page, body=6, padding=2, orphans=orphans,
                                  allow_empty_first_page=allow_empty_first_page, **kwargs)
        
        paginator.num_pages

        sort_key = self.order.lstrip('-')
        if sort_key in self.sql_sort:
            queryset = queryset.order_by(self.order, 'id')
        elif sort_key == 'group':
            queryset = queryset.order_by(self.order + '__name', 'id')
        
        paginator.object_list = queryset

    @cached_property
    def profile(self):
        if not self.request.user.is_authenticated:
            return None
        return self.request.user

    def get_queryset(self):
        filter = Q(is_public=True)
        if self.request.user.is_authenticated:
            filter |= Q(authors=self.profile)
        
        queryset = Problem.objects.filter(filter).select_related('group').defer('description')
        if not self.request.user.has_perm('education.see_organization_problem'):
            filter = Q(is_organization_private=False)
            if self.profile is not None:
                filter |= Q(organizations__in=self.profile.organizations.all())
            queryset = queryset.filter(filter)
        
        if self.category is not None:
            queryset = queryset.filter(group__id=self.category)

        self.pre_difficult_queryset = queryset
        if self.difficult_start is not None:
            queryset = queryset.filter(difficult__gte=self.difficult_start)
        if self.difficult_end is not None:
            queryset = queryset.filter(difficult__lte=self.difficult_end)
        
        return queryset.distinct()

    def get_noui_slider_difficult(self):
        difficult = sorted(self.pre_difficult_queryset.values_list('difficult', flat=True).distinct())
        if not difficult:
            return 0, 0, {}
        if len(difficult) == 1:
            return difficult[0], difficult[0], {
                'min': difficult[0] - 1,
                'max': difficult[0] + 1,
            }

        start, end = difficult[0], difficult[-1]
        if self.point_start is not None:
            start = self.point_start
        if self.point_end is not None:
            end = self.point_end
        difficult_map = {0.0: 'min', 1.0: 'max'}
        size = len(difficult) - 1
        return start, end, {difficult_map.get(i / size, '%.2f%%' % (100 * i / size,)): j for i, j in enumerate(difficult)}
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category

        context.update(self.get_sort_paginate_context())
        context.update(self.get_sort_context())
        context['difficult_start'], context['difficult_end'], context['difficult_values'] = self.get_noui_slider_difficult()

        return context
    

    def GET_with_session(self, request, key):
        if not request.GET:
            return request.session.get(key, False)
        return request.GET.get(key, None) == '1'

    def setup_problem_list(self, request):
        self.category = None

        self.all_sorts = set(self.all_sorts)

        self.category = safe_int_or_none(request.GET.get('category'))
        self.difficult_start = safe_float_or_none(request.GET.get('difficult_start'))
        self.difficult_end = safe_float_or_none(request.GET.get('difficult_end'))
    
    def get(self, request, *args, **kwargs):
        self.setup_problem_list(request)

        try:
            super().get(request, *args, **kwargs)
        except ProgrammingError as e:
            return generic_message(request, 'FTS syntax error', e.args[1], status=400)


class ProblemDetail(ProblemMixin, DetailView):
    context_object_name = 'problem'
    template_name = 'problem/problem.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # authed = user.is_authenticated
        context['can_edit'] = self.object.is_editable_by(user)

        context['title'] = self.object.name
        context['description'] = self.object.description

        if user.is_staff or user.is_superuser:
            context['answer'] = Answer.objects.filter(problem=object).values_list('description')



