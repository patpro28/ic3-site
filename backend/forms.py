from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import password_validation

from backend.models import Profile, User
from backend.models.organization import Organization
from backend.widgets.martor import MartorWidget
from backend.widgets.select2 import UserMultipleWidget
from backend.widgets.fields import SelectMultiple


class EditProfileForm(forms.ModelForm):

  class Meta:
    model = Profile
    fields = ['about']
    widgets = {
      'about': MartorWidget(attrs={'data-markdownfy-url': reverse_lazy('markdown_preview')}),
    }


class RegisterForm(forms.ModelForm):
  # fullname = forms.CharField(max_length=30, required=True, label=_('Fullname'))
  username = forms.RegexField(regex=r'^(?=.{4,30}$)(?![_.])(?!.*[_.]{2})[a-z0-9._]+(?<![_.])$', max_length=30, label=_('Username'),
                              error_messages={'invalid': _('A username must contain lower latinh letters, '
                                                             'numbers, min length = 4, max length = 30')})
  first_name = forms.CharField(max_length=30, required=True, label=_('First name'))
  last_name = forms.CharField(max_length=30, required=True, label=_('Last name'))
  password = forms.CharField(
      label=_("Password"),
      strip=False,
      widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
      help_text=password_validation.password_validators_help_text_html(),
  )

  class Meta:
    model = User
    fields = ['username', 'password', 'first_name', 'last_name']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['username'].widget.attrs['autofocus'] = True

  def save(self, commit=True):
    user = super().save(commit=False)
    user.set_password(self.cleaned_data["password"])
    if commit:
      user.save()
    return user


class LoginForm(forms.Form):
  username = forms.CharField(label=_('Username'), max_length=30, required=True)
  password = forms.CharField(label=_('Password'), max_length=30, required=True, widget=forms.PasswordInput)


class EditOrganizationForm(forms.ModelForm):
  class Meta:
    model = Organization
    fields = ['about', 'logo', 'admins']

    widgets = {
      'admins': SelectMultiple,
      'about': MartorWidget(attrs={'data-markdownfy-url': reverse_lazy('description_preview')}),
    }