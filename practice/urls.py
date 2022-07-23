from django.urls import path, include
from .views import PracticeView, PracticeTaskView, AllSubmissions

app_name = 'practice'

urlpatterns = [
  path('', PracticeView.as_view(), name="practice_form"),
  path('<int:pk>/', PracticeTaskView.as_view(), name="practice_task"),
  path('submissions/', AllSubmissions.as_view(), name='all_submissions')
]
