from django.conf import settings
from django.urls import reverse
from django.views.generic import ListView
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from backend.models.profile import Profile
from education.models.contest import Contest

from socical.models import Blog
from backend.utils.diggpaginator import DiggPaginator

class PostList(ListView):
  model = Blog
  paginate_by = 10
  context_object_name = 'blogs'
  template_name = ''
  title = None

  def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True, **kwargs):
    return DiggPaginator(queryset, per_page, body=6, padding=2, orphans=orphans, 
                        allow_empty_first_page=allow_empty_first_page, **kwargs)
  
  def get_queryset(self):
      return Blog.objects.filter(visible=True, publish__lte=timezone.now()).order_by('-publish')
    
  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['title'] = self.title or _('Page %d of Posts') % context['page_obj'].number
    context['first_page_href'] = reverse('education:home')

    now = timezone.now()

    visible_contests = Contest.get_visible_contests(self.request.user).filter(is_visible=True) \
                                  .order_by('start_time')
    
    context['current_contests'] = visible_contests.filter(start_time__lte=now, end_time__gt=now)
    context['future_contests'] = visible_contests.filter(start_time__gt=now)

    users = Profile.objects.all().order_by('-point')
    if users.count() > 10:
      users = users[:10]
    i = 0
    context['ranking'] = []
    for user in users:
      context['ranking'].append({
        'rank': i,
        'user': user
      })
      i += 1
    while i < 10:
      context['ranking'].append({
        'rank': i,
        'user': None,
      })
      i += 1
    # context['page_prefix'] = reverse('blog_page_list')
    
    return context