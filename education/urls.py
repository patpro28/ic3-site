from django.urls import include, path

from education.views.problem import ProblemDetail, ProblemList, ProblemLevelList

from .views import *
from emath.urls import paged_list_view

app_name = 'education'

urlpatterns = [
    path('problems/', paged_list_view(ProblemList, 'problem_list')),
    path('problems/<slug:level>/', paged_list_view(ProblemLevelList, 'problem_level_list')),
    path('problem/<slug:problem>/', include([
        path('', ProblemDetail.as_view(), name='problem_detail')
    ]))
]
