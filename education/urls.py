from django.urls import include, path

from education.views.problem import ProblemDetail, ProblemList, ProblemLevelList
from education.views import submission, contest

from .views import *
from emath.urls import paged_list_view

from social.views import PostList

app_name = 'education'

urlpatterns = [
    path('', PostList.as_view(template_name="home.html"), name='home'),
    path('problems/', paged_list_view(ProblemList, 'problem_list')),
    path('problems/<slug:level>/', paged_list_view(ProblemLevelList, 'problem_level_list')),
    path('problem/<slug:problem>/', include([
        path('', ProblemDetail.as_view(), name='problem_detail')
    ]))
]

urlpatterns += [
    path('contests/', paged_list_view(contest.ContestList, 'contest_list')),
    path('contest/<slug:contest>/', include([
        path('', contest.ContestDetail.as_view(), name="contest_detail"),
        path('ranking/', contest.ContestRanking.as_view(), name='contest_ranking'),
        path('join/', contest.ContestJoin.as_view(), name='contest_join'),
        path('leave/', contest.ContestLeave.as_view(), name='contest_leave'),
        path('task/', contest.ContestTaskView.as_view(), name='contest_task')
    ]))
]

urlpatterns += [
    path('submissions/', paged_list_view(submission.AllSubmissions, 'all_submissions')),
    path('submission/<int:pk>/', submission.SubmissionStatus.as_view(), name='submission_status')
]