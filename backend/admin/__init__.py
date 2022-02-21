from django.contrib import admin

from backend.models import Profile, Organization

from .profile import *

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Organization)