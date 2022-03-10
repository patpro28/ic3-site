from django_select2 import forms
from backend.models import Profile

class UserSelect2WidgetMixin(object):
  def __init__(self, *args, **kwargs):
    kwargs['data-view'] = 'backend:user-select2-view'
    # print(kwargs)
    super().__init__(*args, **kwargs)

class UserWidget(UserSelect2WidgetMixin, forms.ModelSelect2Widget):
  model = Profile
  search_fields = [
    "username__icontains",
    "fullname__icontains",
  ]


class UserMultipleWidget(UserSelect2WidgetMixin, forms.ModelSelect2MultipleWidget):
  model = Profile
  search_fields = [
    "username__icontains",
    "fullname__icontains",
  ]