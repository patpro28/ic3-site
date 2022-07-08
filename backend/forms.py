from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import password_validation

from backend.models import Profile
from backend.models.organization import Organization
from backend.widgets.martor import MartorWidget
from backend.widgets.select2 import UserMultipleWidget
from backend.widgets.fields import SelectMultiple
from semantic_admin.widgets import SemanticTextInput, SemanticSelectMultiple


class EditProfileForm(forms.ModelForm):

  class Meta:
    model = Profile
    fields = ["fullname", 'email', 'about', 'is_active', 'is_staff', 'is_superuser', 'groups']
    widgets = {
      'fullname': SemanticTextInput,
      'about': MartorWidget(attrs={'data-markdownfy-url': reverse_lazy('markdown_preview')}),
      'groups': SelectMultiple
    }


class RegisterForm(forms.ModelForm):
  error_messages = {
    'password_mismatch': _("The two password fields didn\'t match."),
  }
  # fullname = forms.CharField(max_length=30, required=True, label=_('Fullname'))
  username = forms.RegexField(regex=r'^(?=.{4,30}$)(?![_.])(?!.*[_.]{2})[a-z0-9._]+(?<![_.])$', max_length=30, label=_('Username'),
                              error_messages={'invalid': _('A username must contain lower latinh letters, '
                                                             'numbers, min length = 4, max length = 30')})
  password1 = forms.CharField(
      label=_("Password"),
      strip=False,
      widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
      help_text=password_validation.password_validators_help_text_html(),
  )
  password2 = forms.CharField(
      label=_("Password confirmation"),
      widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
      strip=False,
      help_text=_("Enter the same password as before, for verification."),
  )

  class Meta:
    model = Profile
    fields = ['username', 'password1', 'password2']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['username'].widget.attrs['autofocus'] = True

  def clean_password2(self):
    password1 = self.cleaned_data.get("password1")
    password2 = self.cleaned_data.get("password2")
    if password1 and password2 and password1 != password2:
      raise forms.ValidationError(
        self.error_messages['password_mismatch'],
        code='password_mismatch',
      )
    return password2

  def save(self, commit=True):
    user = super().save(commit=False)
    user.set_password(self.cleaned_data["password1"])
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