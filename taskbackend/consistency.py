import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")

from config.configuration import config_path_work

import django
django.setup()

from earkweb.models import InformationPackage

def main():
    # ips without working directory
    ips = InformationPackage.objects.all()
    for ip in ips:
        if not os.path.exists(ip.work_dir):
            os.makedirs(ip.work_dir)
            print("Missing working directory created: %s" % ip.work_dir)
    # working directory without ip
    wdirs = os.listdir("%s" % config_path_work)
    for wdir in wdirs:
        try:
            InformationPackage.objects.get(uid=wdir)
        except:
            import shutil
            if wdir:
                print("Orphan directory: %s/%s" % (config_path_work, wdir))


if __name__ == "__main__":
    main()
