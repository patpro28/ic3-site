from django import forms

class AlwaysChangedModelForm(forms.ModelForm):
    def has_changed(self) -> bool:
        return True