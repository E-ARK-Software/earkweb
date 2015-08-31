from django import forms
from earkcore.models import InformationPackage
from workflow.models import WorkflowModules
from workflow.models import Wirings

class PackageWorkflowModuleSelectForm(forms.Form):
    ips = forms.ModelChoiceField(label="Information package", queryset=InformationPackage.objects.all())
    wfs = forms.ModelChoiceField(label="Workflow module", queryset=WorkflowModules.objects.all())
    wiref = forms.ModelChoiceField(label="Wirings", queryset=Wirings.objects.all())