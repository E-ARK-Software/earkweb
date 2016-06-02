import inspect
import pydoc
import re
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")

from config.configuration import config_path_work

import django
django.setup()

from earkcore.models import InformationPackage

def main():
    # ips without working directory
    ips = InformationPackage.objects.all()
    for ip in ips:
        if not os.path.exists(ip.path):
            os.makedirs(ip.path)
            print "Missing working directory created: %s" % ip.path
    # working directory without ip
    wdirs = os.listdir("%" % config_path_work)
    for wdir in wdirs:
        try:
            InformationPackage.objects.get(uuid=wdir)
        except:
            import shutil
            if wdir:
                print "Orphan directory: %/%s" % (config_path_work, wdir)
if __name__ == "__main__":
    main()
