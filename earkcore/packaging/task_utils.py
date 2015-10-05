import os
import glob


def get_deliveries(path, task_logger):
    tar_files = glob.glob("%s/*.tar" % path)
    task_logger.addinfo("Tar files found: %s" % tar_files)
    deliveries = {}
    for tar_file in tar_files:
        tar_base_name, _ = os.path.splitext(tar_file)
        delivery_file = "%s.xml" % tar_base_name
        if os.path.exists(delivery_file):
            deliveries[tar_base_name] = {"delivery_xml": delivery_file, "tar_file": tar_file}
    return deliveries
