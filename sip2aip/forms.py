from django import forms
from earkcore.models import InformationPackage
from workers.tasks import SIPPackaging
from workflow.models import WorkflowModules
from workflow.models import Wirings

class PackageWorkflowModuleSelectForm(forms.Form):
    ttype = 6
    ips = forms.ModelChoiceField(label="Information package", queryset=InformationPackage.objects.all())
    wfs = forms.ModelChoiceField(label="Task", queryset=WorkflowModules.objects.extra(where=["ttype & %d" % ttype]).order_by('ordval'))
    #wiref = forms.ModelChoiceField(label="Workflow", queryset=Wirings.objects.all())


class AIPtoDIPWorkflowModuleSelectForm(PackageWorkflowModuleSelectForm):
    ttype = 4
    ips = forms.ModelChoiceField(label="Information package", queryset=InformationPackage.objects.all())
    wfs = forms.ModelChoiceField(label="Task", queryset=WorkflowModules.objects.extra(where=["ttype & %d" % ttype]).order_by('ordval'))
    #wiref = forms.ModelChoiceField(label="Workflow", queryset=Wirings.objects.all())


class SIPtoAIPWorkflowModuleSelectForm(PackageWorkflowModuleSelectForm):
    ttype = 2
    ips = forms.ModelChoiceField(label="Information package", queryset=InformationPackage.objects.all())
    wfs = forms.ModelChoiceField(label="Task", queryset=WorkflowModules.objects.extra(where=["ttype & %d" % ttype]).order_by('ordval'))
    #wiref = forms.ModelChoiceField(label="Workflow", queryset=Wirings.objects.all())

class SIPCreationPackageWorkflowModuleSelectForm(PackageWorkflowModuleSelectForm):
    ttype = 1
    ips = forms.ModelChoiceField(label="Information package", queryset=InformationPackage.objects.all())
    wfs = forms.ModelChoiceField(label="Task", queryset=WorkflowModules.objects.extra(where=["ttype & %d" % ttype]).order_by('ordval'))
    #wiref = forms.ModelChoiceField(label="Workflow", queryset=Wirings.objects.all())

class UploadSIPDeliveryForm(forms.Form):
    sip_tar_package = forms.FileField(label='Local SIP TAR package')
    sip_delivery_xml = forms.FileField(label='SIP Delivery XML file')