import os, sys
import time, os

# initialise django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")
import django
django.setup()

from config.config import root_dir
from config import params
from earkcore.utils import randomutils
from tasklogger import TaskLogger
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
tl.addinfo("Developing some task")

print ip.path
print ip_work_dir
print tl.fin().log
print tl.fin().success

