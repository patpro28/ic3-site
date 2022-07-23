from django import forms
from education.models import Level
from django.utils.translation import gettext_lazy as _
from semantic_admin.widgets import SemanticSelect

class PracticeForm(forms.Form):
  level = forms.ChoiceField(label=_('level'), 
                            choices=Level.objects.all().values_list('id', 'name'), 
                            required=True,
                            widget=SemanticSelect
                            )
