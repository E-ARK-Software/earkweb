import os
import glob
import re

def get_deliveries(path, task_logger):
    #tar_files = glob.glob("%s/*.tar" % path)
    package_files = [f for f in os.listdir(path) if re.search(r'.*\.(zip|tar)$', f)]
    task_logger.addinfo("Package files found: %s" % package_files)
    deliveries = {}
    for package_file in package_files:
        tar_base_name, _ = os.path.splitext(package_file)
        delivery_file = os.path.join(path, ("%s.xml" % tar_base_name))
        task_logger.addinfo("Looking for delivery file: %s" % delivery_file)
        if os.path.exists(delivery_file):
            deliveries[tar_base_name] = {"delivery_xml": delivery_file, "package_file": package_file}
        else:
            task_logger.addinfo("Warning: no delivery file found for package: %s" % tar_base_name)
    return deliveries
