from django import forms
from earkcore.models import InformationPackage
from workflow.models import WorkflowModules
from workflow.models import Wirings

class PackageWorkflowModuleSelectForm(forms.Form):
    ttype = 3
    ips = forms.ModelChoiceField(label="Information package", queryset=InformationPackage.objects.all())
    wfs = forms.ModelChoiceField(label="Task", queryset=WorkflowModules.objects.extra(where=["ttype & %d" % ttype]).order_by('ordval'))
    wiref = forms.ModelChoiceField(label="Workflow", queryset=Wirings.objects.all())


class DIPPackageWorkflowModuleSelectForm(PackageWorkflowModuleSelectForm):
    ttype = 2
    ips = forms.ModelChoiceField(label="Information package", queryset=InformationPackage.objects.all())
    wfs = forms.ModelChoiceField(label="Task", queryset=WorkflowModules.objects.extra(where=["ttype & %d" % ttype]).order_by('ordval'))
    wiref = forms.ModelChoiceField(label="Workflow", queryset=Wirings.objects.all())


class SIPPackageWorkflowModuleSelectForm(PackageWorkflowModuleSelectForm):
    ttype = 1
    ips = forms.ModelChoiceField(label="Information package", queryset=InformationPackage.objects.all())
    wfs = forms.ModelChoiceField(label="Task", queryset=WorkflowModules.objects.extra(where=["ttype & %d" % ttype]).order_by('ordval'))
    wiref = forms.ModelChoiceField(label="Workflow", queryset=Wirings.objects.all())

class SIPCreationPackageWorkflowModuleSelectForm(PackageWorkflowModuleSelectForm):
    ttype = 4
    ips = forms.ModelChoiceField(label="Information package", queryset=InformationPackage.objects.all())
    wfs = forms.ModelChoiceField(label="Task", queryset=WorkflowModules.objects.extra(where=["ttype & %d" % ttype]).order_by('ordval'))
    wiref = forms.ModelChoiceField(label="Workflow", queryset=Wirings.objects.all())