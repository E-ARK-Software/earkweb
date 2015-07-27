from django.template import RequestContext, loader

from django.http import HttpResponse
import logging
from models import WorkflowModules
from models import Wirings
logger = logging.getLogger(__name__)

from django.contrib.auth.decorators import login_required

import json
from pprint import pprint

@login_required
def index(request):
    print request.user
    template = loader.get_template('workflow/index.html')
    context = RequestContext(request, {
    })
    return HttpResponse(template.render(context))

@login_required
def workflow_language(request):
    print request.user
    wfdefs = WorkflowModules.objects.all()
    template = loader.get_template('workflow/language.js')
    context = RequestContext(request, {
        'workflow_definitions': wfdefs
    })
    return HttpResponse(template.render(context), content_type='text/plain; charset=utf8')

@login_required
def backend(request):
    """
    Backend of the wiring editor for handling POST requests.
    Methods are 'listWirings', 'saveWiring', 'deleteWiring'.
    :param request: Request
    :return: HttpResponse(status=200, "OK")
    """
    if request.method == "POST":

        try:
            data = json.loads(str(request.body))
            logger.debug("Request (JSON):\n" + json.dumps(data, indent=2))
            if data['method'] == "listWirings":
                wirings = Wirings.objects.all()
                wiringJsons = []
                # each wiring (wiring.working) is returned as a backslash escaped string (substitution variable: working),
                # therefore double quotes in "wiring.working" are backslash escaped.
                for wiring in wirings:
                    wiringJsons.append("""{ "id": "%(id)s", "name": "%(name)s", "working": "%(working)s", "language": "%(language)s" }"""
                                       % { 'name': wiring.name, 'working': (wiring.working).replace('"', '\\"'), 'language': wiring.language, 'id': wiring.id })
                jsonStr = """{"id": 1, "result": [ %(modules)s ], "error": null }""" % { 'modules': (",".join(wiringJsons)) }
                jsonObj = json.loads(jsonStr)
                logger.debug("Response (JSON):\n" + json.dumps(jsonObj, indent=2))
                return HttpResponse(jsonStr)
            if data['method'] == "saveWiring":
                name = data['params']['name']
                working = data['params']['working']
                language = data['params']['language']
                wiring = Wirings.objects.create(language=language,name=name,working=working)
                wiring.save()
            if data['method'] == "deleteWiring":
                name = data['params']['name']
                logger.debug("Delete wiring: %s" % name)
                u = Wirings.objects.get(name=name).delete()
        except Exception:
            logger.error('test', exc_info=True)
        return HttpResponse(status=200)
    else:
        pass
