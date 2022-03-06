from django.conf import settings
from django.urls import reverse
from django.views.generic import ListView
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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
      return Blog.objects.filter(visible=True, publish__lte=timezone.now).order_by('-publish')
    
  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['title'] = self.title or _('Page %d of Posts') % context['page_obj'].number
    context['first_page_href'] = reverse('home')
    context['page_prefix'] = reverse('blog_page_list')
    
    return context