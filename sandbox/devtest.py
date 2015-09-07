import os, sys
import time, os
from earkcore.utils.xmlutils import pretty_xml_string
from lxml import etree, objectify
# initialise django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")
import django
django.setup()

from config.config import root_dir
from config import params
from earkcore.utils import randomutils
from workers.tasklogger import TaskLogger
from earkcore.models import InformationPackage
from earkcore.metadata.premis.PremisManipulate import Premis

def init_task(pk_id, task_name, task_logfile_name):
    start_time = time.time()
    ip = InformationPackage.objects.get(pk=pk_id)
    if not ip.uuid:
        ip.uuid = randomutils.getUniqueID()
    ip_work_dir = os.path.join(params.config_path_work, ip.uuid)
    task_log_file_dir = os.path.join(ip_work_dir, 'metadata')
    task_log_file = os.path.join(task_log_file_dir, "%s.log" % task_logfile_name)
    # create working directory
    if not os.path.exists(ip_work_dir):
        os.mkdir(ip_work_dir)
    # create log directory
    if not os.path.exists(task_log_file_dir):
        os.mkdir(task_log_file_dir)
    tl = TaskLogger(task_log_file)
    return ip, ip_work_dir, tl, start_time


ip, ip_work_dir, tl, start_time = init_task(11, "Test task", "test")

# initial version of PREMIS
with open(root_dir+'/earkresources/PREMIS_skeleton.xml', 'r') as premis_file:
    my_premis = Premis(premis_file)
my_premis.add_agent('earkweb')
my_premis.add_event('AIP Creation', 'earkweb')
my_premis.add_object('file://./submission/PACKAGENAME/METS.xml')
path_premis = os.path.join('/tmp/','PREMIS.xml')
print pretty_xml_string(my_premis.to_string())
with open(path_premis, 'w') as output_file:
    output_file.write(my_premis.to_string())

#print "First version created, now file format identification event"
time.sleep(2)

with open('/tmp/PREMIS.xml', 'r') as premis_file:
    my_premis = Premis(premis_file)
my_premis.add_event('File format identification (PRONOM/fido)', 'earkweb', 'file://./submission/PACKAGENAME/METS.xml')
for obj in my_premis.root.object:
    print obj.objectIdentifier.objectIdentifierValue
    # File format The Pronom Unique Identifier is provided as a as a descendant of the
    # <objectCharacteristics> element in form Persistent Unique Identifier (PUID) 18 based
    # on the PRONOM technical registry. 19 An example is shown in figure 11.
    # <format>
    # <formatRegistry>
    # <formatRegistryName>PRONOM</formatRegistryName>
    # <formatRegistryKey>fmt/101</formatRegistryKey>
    # <formatRegistryRole>identification</formatRegistryRole>
    # </formatRegistry>
    # </format>
    # add pronom identifier (PUID) here to /premis/object/objectCharacteristics/format/formatRegistryKey
    # /premis/object/objectCharacteristics/format/formatRegistryName is always PRONOM
my_premis.add_object('file://./submission/PACKAGENAME/metadata/ead.xml')
path_premis = os.path.join('/tmp/','PREMIS.xml')

with open(path_premis, 'w') as output_file:
    output_file.write(pretty_xml_string(my_premis.to_string()))




