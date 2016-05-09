from django import forms


# class InputPath(forms.Form):
#     input_path = forms.CharField(max_length=300)
#
#
# class JobSelect(forms.Form):
#     JOBS = (
#         ('gerNER', 'NER German'),
#         ('hunNER', 'NER Hungarian'),
#     )
#     job_name = forms.ChoiceField(choices=JOBS, widget=forms.RadioSelect)


class UploadCtrlFile(forms.Form):
    ctrl_file = forms.FileField(label='Select and upload a ToMaR control file:')
