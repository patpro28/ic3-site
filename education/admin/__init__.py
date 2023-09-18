from django.contrib import admin

from .problem import *
from .contest import *
from .course import *
from education.models import Problem, ProblemGroup, Level, Contest, ContestParticipation
from education.models.course import Course

admin.site.register(Problem, ProblemAdmin)
admin.site.register(ProblemGroup, ProblemGroupAdmin)
admin.site.register(Level, LevelAdmin)
admin.site.register(Contest, ContestAdmin)
admin.site.register(ContestParticipation, ContestParticipationAdmin)
admin.site.register(Course, CourseAdmin)