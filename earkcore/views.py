import os
from django.views.generic.detail import DetailView
from django.contrib.auth.decorators import login_required
from config.params import config_path_work
from config.params import config_path_reception

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, HttpResponseServerError

from earkcore.models import InformationPackage

class InformationPackageDetailView(DetailView):
    model = InformationPackage
    template_name = 'earkcore/ip_detail.html'

@login_required
@csrf_exempt
def check_folder_exists(request, folder):
    path = os.path.join(config_path_work, folder)
    return HttpResponse(str(os.path.exists(path)).lower())

@login_required
@csrf_exempt
def check_submission_exists(request, packagename):
    # submission already exists, if a delivery XML is in the reception folder
    path = os.path.join(config_path_reception, ("%s.xml" % packagename))
    return HttpResponse(str(os.path.exists(path)).lower())