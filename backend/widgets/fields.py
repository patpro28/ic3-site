from django.forms.widgets import (
  TextInput as OldTextInput,
  CheckboxInput as OldCheckboxInput,
  DateInput as OldDateInput,
  DateTimeInput as OldDateTimeInput,
  NumberInput as OldNumberInput,
  TimeInput as OldTimeInput,
  EmailInput as OldEmailInput,
  HiddenInput as OldHiddenInput,
  Textarea as OldTextarea,
  Select as OldSelect,
  RadioSelect as OldRadioSelect,
  CheckboxSelectMultiple as OldCheckboxSelectMultiple,
  SelectMultiple as OldSelectMultiple
)

class TextInput(OldTextInput):
  template_name = 'admin/widgets/text.html'

class CheckboxInput(OldCheckboxInput):
  template_name = 'admin/widgets/checkbox.html'

class DateInput(OldDateInput):
  template_name = 'admin/widgets/date.html'

class DateTimeInput(OldDateTimeInput):
  template_name = 'admin/widgets/datatime.html'

class Textarea(OldTextarea):
  template_name = 'admin/widgets/textarea.html'

class Select(OldSelect):
  template_name = 'admin/widgets/select.html'
  option_template_name = 'admin/widgets/select_option.html'

class SelectMultiple(OldSelectMultiple, Select):
  pass

class RadioSelect(OldRadioSelect):
  template_name = 'admin/widgets/radio.html'
  option_template_name = 'admin/widgets/radio_option.html'

class CheckboxSelectMultiple(OldCheckboxSelectMultiple):
  template_name = 'admin/widgets/checkbox_select.html'
  option_template_name = 'admin/widgets/checkbox_option.html'

class TimeInput(OldTimeInput):
  template_name = 'admin/widgets/time.html'