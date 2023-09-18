from django import forms
from education.models import Level
from django.utils.translation import gettext_lazy as _

class PracticeForm(forms.Form):
  level = forms.ChoiceField(label=_('level'), 
                            choices=(), 
                            required=True,
                            )

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['level'].choices = [(level.id, level.name) for level in Level.objects.all()]      
