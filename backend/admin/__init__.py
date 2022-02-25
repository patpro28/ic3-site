from django.contrib import admin

from backend.models import Profile, Organization, NavigationBar

from .profile import *
from .organization import *

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(NavigationBar)