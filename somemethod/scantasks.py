import tasks
import inspect
import pydoc
import re
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")

import django
django.setup()

from workflow.models import WorkflowModules

class Param(object):
    def __init__(self, type, name, descr):
        self.type = type
        self.name = name
        self.descr = descr

class InputParam(Param):
    pass

class ReturnParam(Param):
    pass

class TaskScanner(object):

    task_modules = dict()

    def __init__(self, taskmodule):
        self.taskmodule = taskmodule
        methodList = [item for item in dir(taskmodule)]
        for item in methodList:
            if inspect.isclass(getattr(tasks, item)) and str(item) != "Task":
                c = getattr(tasks, item)
                runmethod = getattr(c, "run")
                rundoc = runmethod.__doc__
                params = []
                doclist = rundoc.split('\n')
                paramline = ""
                for dlitem in doclist:
                    paramline += dlitem
                    if "@param" in dlitem:
                        match = re.search('@type (?P<tpname>.*): (?P<datatype>.*)@param (?P<ppname>.*): (?P<description>.*)', paramline)
                        type = match.group('datatype').strip()
                        name = match.group('tpname').strip()
                        descr = match.group('description').strip()
                        params.append(InputParam(type, name, descr))
                        paramline = ""
                    elif "@return:" in dlitem:
                        match = re.search('@rtype:\s*(?P<rtype>.*)@return:\s*(?P<descr>.*)', paramline)
                        type = match.group('rtype').strip()
                        descr = match.group('descr').strip()
                        params.append(ReturnParam(type, None, descr))
                        paramline = ""
                self.task_modules[str(item)] = params

class WireItLanguageModules(object):

    def __init__(self, task_modules):
        self.task_modules = task_modules

    language_module_template = """
    {
        "name": "%(module_name)s",
        "container": {
            "xtype": "WireIt.FormContainer",
            "title": "%(module_name)s",
            "icon": "/static/earkweb/workflow/wireit/res/icons/valid-xml.png",
            "collapsible": true,
            "drawingMethod": "arrows",
            "fields": [
                {"type":"string", "inputParams": {"label": "check well-formed", "name": "param"}},
            ],
            "terminals": [
                {"name": "_INPUT", "direction": [0,0], "offsetPosition": {"left": 160, "top": -13 },"ddConfig": {"type": "input","allowedTypes": ["output"]}, "nMaxWires": 1,  "drawingMethod": "arrows" },
                {"name": "_OUTPUT", "direction": [0,0], "offsetPosition": {"left": 160, "bottom": -13 },"ddConfig": {"type": "output","allowedTypes": ["input"]}}
            ],
            "legend": "%(module_name)s",
            "drawingMethod": "arrows"
        }
    },
    """

    language_module_inputs_template = """
        {inputParams: {label: 'Working directory', name: 'working_dir', required: true, value:'/home/shs/eark/' } }
    """

    def register_language_modules(self):
        WorkflowModules.objects.all().delete()
        for module_name, module_params in self.task_modules.iteritems():
            print module_name
            # for module_param in module_params:
                # if isinstance(module_param, InputParam):
                #     print module_param.name
            model_def = self.language_module_template % { 'module_name': module_name }
            workflow_module = WorkflowModules(identifier=module_name, model_definition=model_def)
            workflow_module.save()
            print "maybe done ..."




def main():
    task_modules = TaskScanner(tasks).task_modules
    wirelangmod = WireItLanguageModules(task_modules)
    wirelangmod.register_language_modules()


if __name__ == "__main__":
    main()