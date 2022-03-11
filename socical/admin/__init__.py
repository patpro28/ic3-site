from django.contrib import admin

from .blog import *
from socical.models import Blog

admin.site.register(Blog, BlogPostAdmin)