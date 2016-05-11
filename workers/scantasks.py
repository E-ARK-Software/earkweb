
import inspect
import pydoc
import re
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")

import django
django.setup()

import tasks

from workflow.models import WorkflowModules
from earkcore.models import InformationPackage


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
    """
    Scan tasks module for Celery tasks. The run method documentation is parsed to provide
    input parameter documentation.
    """

    task_modules = dict()

    def register_method(self, method_name, c, item):
        runmethod = getattr(c, method_name)
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

    def __init__(self, taskmodule):
        """
        Scanning celery tasks and parsing run method documentation is done here in the constructor.
        """
        self.taskmodule = taskmodule
        methodList = [item for item in dir(taskmodule)]
        for item in methodList:
            if inspect.isclass(getattr(tasks, item)) and str(item) != "Task":# and str(item) != "DefaultTask":
                c = getattr(tasks, item)
                try:
                    self.register_method("run", c, item)
                    self.register_method("run_task", c, item)
                except AttributeError:
                    pass

class WireItLanguageModules(object):
    """
    Build language modules from task module objects based on JSON template.
    """

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
                %(input_params)s
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
        {"type":"%(type)s", "inputParams": {"label": "%(descr)s", "name": "%(name)s"}},
    """

    def register_language_modules(self):
        """
        Register tasks as language modules in the database. All records are deleted first,
        then available celery tasks are stored as language modules.
        """
        module_list = []
        for module_name, module_params in self.task_modules.iteritems():
            input_params = ""
            exp = 0; sxs = 0; err = 0
            module_list.append(module_name)
            print module_name
            for module_param in module_params:
                if isinstance(module_param, InputParam):
                    descr = "Task configuration" if module_param.descr.startswith("order") else module_param.descr
                    input_params += self.language_module_inputs_template % { 'name': module_param.name, 'descr': descr, 'type': module_param.type}
                    print module_param.name
                    if module_param.name.startswith('tc'):
                        match = re.search('order:(?P<ord>.*),type:(?P<typ>.*),stage:(?P<stg>.*)',module_param.descr)
                        ord = int(match.group('ord').strip())
                        typ = int(match.group('typ').strip())
                        stg = int(match.group('stg').strip())
                        print "%s %s %s" % (ord, typ, stg)

            model_def = self.language_module_template % { 'module_name': module_name, 'input_params': input_params }

            if WorkflowModules.objects.filter(identifier=module_name).count() == 1:
                existing_wf_module = WorkflowModules.objects.get(identifier=module_name)
                if existing_wf_module.ordval != ord or existing_wf_module.ttype != typ or existing_wf_module.tstage != stg:
                    existing_wf_module.ordval = ord
                    existing_wf_module.ttype = typ
                    existing_wf_module.tstage = stg
                    existing_wf_module.save()
                    print "Module parameters updated: %s (ordval=%d, ttype=%d, tstage=%d)" % (existing_wf_module.identifier, ord, typ, stg)
            else:
                workflow_module = WorkflowModules(identifier=module_name, model_definition=model_def, ordval=ord, ttype=typ, tstage=stg)
                print "New module created: %s" % module_name
                workflow_module.save()

        # check modules removed
        all_wf_modules = WorkflowModules.objects.all()
        for wf_mod in all_wf_modules:
            if wf_mod.identifier not in module_list:
                # check information packages where 'last_task' corresponds with the removed module and set it to DefaultTask
                print "The task for this module was removed: %s" % wf_mod.identifier
                ips_removed_task = InformationPackage.objects.filter(last_task=wf_mod.identifier)
                default_module = WorkflowModules.objects.get(identifier=tasks.DefaultTask.__name__)
                for ip in ips_removed_task:
                    print "- IP with process id '%s' (%s) with last task '%s' set to 'DefaultTask'" % (ip.uuid, ip.packagename, ip.last_task)
                    print "  Note that the last_task is not updated in state.xml!"
                    ip.last_task = default_module
                    ip.save()
                # delete module of removed task
                wf_mod.delete()


def main():
    task_modules = TaskScanner(tasks).task_modules
    for module_name, module_params in task_modules.iteritems():
        print "Module found in tasks.py: %s" % module_name
    wirelangmod = WireItLanguageModules(task_modules)
    wirelangmod.register_language_modules()


if __name__ == "__main__":
    main()