import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")
import django
django.setup()


from earkcore.storage.pairtreestorage import PairtreeStorage
from earkcore.models import InformationPackage
from workflow.models import WorkflowModules
from config.configuration import config_path_storage
from django.core.exceptions import ObjectDoesNotExist

if __name__ == "__main__":
    ps = PairtreeStorage(config_path_storage)
    p_list = ps.latest_version_ip_list()
    for p in p_list:
        print p['id'] + " (" + p['version'] + "):" + os.path.join(config_path_storage, p['path'])
        try:
            ip = InformationPackage.objects.get(identifier=p['id'])
            ip.storage_loc = os.path.join(config_path_storage, str(p['path']))
            ip.save()
        except ObjectDoesNotExist:
            InformationPackage.objects.create(
                path="",
                uuid="",
                identifier=p['id'],
                storage_loc=os.path.join(config_path_storage, p['path']),
                statusprocess=0,
                packagename="",
                last_task=WorkflowModules.objects.get(identifier="IPClose")
            )
    p_list_ids = map(lambda x: x['id'], p_list)
    ips = InformationPackage.objects.all()
    for ip in ips:
        if ip.storage_loc != '':
            if not os.path.exists(ip.storage_loc):
                print "Object is not accessible: %s (unsetting storage_loc)" % ip.identifier
                ip.storage_loc = ''
                ip.save()
            try:
                ps.get_object_path(ip.identifier)
            except ValueError:
                print "Cant get object: %s (identifier changed, unsetting storage_loc)" % ip.identifier
                ip.storage_loc = ''
                ip.save()







