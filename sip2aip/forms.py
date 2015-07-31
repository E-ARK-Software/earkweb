from django import forms
from earkcore.models import InformationPackage

class SomeOtherForm(forms.Form):
    your_name = forms.CharField(label='Your names', max_length=100)
    testen = forms.CharField(label='otherfield', max_length=100)
    field1 = forms.ModelChoiceField(label="test", queryset=InformationPackage.objects.all())