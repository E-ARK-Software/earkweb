import os
from earkcore.utils.fileutils import sub_dirs


def get_last_submission_path(ip_root_path):
    submiss_dir = 'submission'
    submiss_path = os.path.join(ip_root_path, submiss_dir)
    if os.path.exists(os.path.join(submiss_path, "METS.xml")):
        return submiss_path
    else:
        submiss_subdirs = sub_dirs(submiss_path)
        if submiss_subdirs and len(submiss_subdirs) > 0:
            # get last folder (possible submission update folders - sorted!)
            submiss_path = os.path.join(submiss_path, submiss_subdirs[-1])
            if os.path.exists(os.path.join(submiss_path, "METS.xml")):
                return submiss_path
    return None


def get_first_ip_path(wd_root_path):
    if os.path.exists(os.path.join(wd_root_path, "METS.xml")):
        return wd_root_path
    else:
        wd_sub_dirs = sub_dirs(wd_root_path)
        if wd_sub_dirs and len(wd_sub_dirs) > 0:
            # get last folder (possible submission update folders - sorted!)
            for wd_sub_dir in wd_sub_dirs:
                mets_abs_path = os.path.join(wd_root_path, wd_sub_dir, "METS.xml")
                if os.path.exists(mets_abs_path):
                    return os.path.join(wd_root_path, wd_sub_dir)
