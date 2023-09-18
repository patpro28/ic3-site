from django.views.generic import DetailView

from education.models import Course
from backend.utils.views import TitleMixin

class CourseDetailView(TitleMixin, DetailView):
    model = Course
    template_name = 'education/course_detail.html'
    context_object_name = 'course'
    
    def get_title(self):
        return self.object.name