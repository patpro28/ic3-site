from django.contrib import admin

from .problem import *
from education.models import Problem, ProblemGroup, Level

admin.site.register(Problem, ProblemAdmin)
admin.site.register(ProblemGroup, ProblemGroupAdmin)
admin.site.register(Level, LevelAdmin)