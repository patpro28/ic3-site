from django.urls import include, path

from backend.views import select

app_name = 'backend'

urlpatterns = [
  path('select/', include([
    path('profile/', select.UserSearchSelectView.as_view(), name='select_profile'),
    path('problem/', select.ProblemSearchSelectView.as_view(), name='select_problem'),
    path('user/', select.UserSelectView.as_view(), name='user-select2-view')
  ]))
]
