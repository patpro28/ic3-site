from django.contrib import admin

from .problem import *
from education.models import Problem, ProblemGroup

admin.site.register(Problem, ProblemAdmin)
admin.site.register(ProblemGroup, ProblemGroupAdmin)