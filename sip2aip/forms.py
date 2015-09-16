from django import forms
from earkcore.models import InformationPackage
from workflow.models import WorkflowModules
from workflow.models import Wirings

class PackageWorkflowModuleSelectForm(forms.Form):
    ips = forms.ModelChoiceField(label="Information package", queryset=InformationPackage.objects.all())
    wfs = forms.ModelChoiceField(label="Task", queryset=WorkflowModules.objects.all().order_by('ordval'))
    wiref = forms.ModelChoiceField(label="Workflow", queryset=Wirings.objects.all())