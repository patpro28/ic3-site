from django.db.models import Q, F
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.encoding import smart_str
from django.views.generic.list import BaseListView

from backend.templatetags.gravatar import gravatar
from backend.models import Profile, Organization
from education.models import Problem, Contest

def _get_user_queryset(term):
  queryset = Profile.objects
  if term.endswith(' '):
    queryset = queryset.filter(username=term.strip())
  else:
    queryset = queryset.filter(username__icontains=term)
  # print(queryset)
  return queryset


class SelectView(BaseListView):
  paginate_by = 20

  def get(self, request, *args, **kwargs):
    self.request = request
    self.term = kwargs.get('term', request.GET.get('term', ''))
    # print(self.term)
    self.object_list = self.get_queryset()
    context = self.get_context_data()

    return JsonResponse({
      'results': [
        {
          'description': smart_str(self.get_name(obj)),
          'id': obj.pk,
        } for obj in context['object_list']
      ],
      'more': context['page_obj'].has_next()
    })
  
class UserSelectView(SelectView):
  def get_queryset(self):
    return _get_user_queryset(self.term).only('id')
    
  def get_name(self, obj):
    return obj.username

class UserSearchSelectView(BaseListView):
  paginate_by = 20

  def get_queryset(self):
    return _get_user_queryset(self.term)

  def get(self, request, *args, **kwargs):
    self.request = request
    self.kwargs = kwargs
    self.term = kwargs.get('term', request.GET.get('term', ''))
    self.gravatar_size = request.GET.get('gravatar_size', 128)
    self.gravatar_default = request.GET.get('gravatar_default', None)

    self.object_list = self.get_queryset()

    context = self.get_context_data()

    return JsonResponse({
      'results': [
        {
          'user': user.username,
          'id': user.pk,
          'gravatar_url': gravatar(user, self.gravatar_size, self.gravatar_default),
          'display_rank': user.display_rank
        } for user in context['object_list']
      ],
      'more': context['page_obj'].has_next(),
    })
  
  def get_name(self, obj):
    return str(obj)


class ProblemSearchSelectView(BaseListView):
  paginate_by = 20
  
  def get_queryset(self):
    return Problem.objects.filter(
      Q(code__icontains=self.term) or Q(name__icontains=self.term)
    )
  
  def get(self, request, *args, **kwargs):
    self.request = request
    self.kwargs = kwargs
    self.term = kwargs.get('term', request.GET.get('term', ''))
    self.level = request.GET.get('level', None)
    queryset = self.get_queryset()

    if self.level is not None:
      queryset = queryset.filter(level__code=self.level)

    self.object_list = self.get_queryset().values_list('code', 'name', 'level__name')
    # print(self.object_list)

    context = self.get_context_data()

    return JsonResponse({
      'results': [
        {
          'code': code,
          'name': name,
          'level': level,
          'url': reverse('education:problem_detail', kwargs={'problem': code})
        } for code, name, level in context['object_list']
      ]
    })

  def get_name(self, obj):
    return str(obj)
