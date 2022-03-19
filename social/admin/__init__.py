from django.contrib import admin

from .blog import *
from social.models import Blog

admin.site.register(Blog, BlogPostAdmin)