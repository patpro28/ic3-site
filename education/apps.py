from MySQLdb import DatabaseError
from django.apps import AppConfig


class EducationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'education'

    def ready(self) -> None:
        from . import signals

        from .models import Problem, ProblemType

        try:
            for problem in Problem.objects.all():
                for group in problem.types.all():
                    ProblemType.objects.get_or_create(problem=problem, group=group)
        except DatabaseError:
            pass