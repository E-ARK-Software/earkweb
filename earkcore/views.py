from django.views.generic.detail import DetailView

from earkcore.models import InformationPackage

class InformationPackageDetailView(DetailView):
    model = InformationPackage
    template_name = 'earkcore/ip_detail.html'