import os
import pytz, time, datetime
from earkcore.utils.fileutils import remove_protocol

DT_ISO_FORMAT='%Y-%m-%dT%H:%M:%S%z'

def get_file_ctime_iso_date_str(file_path, fmt=DT_ISO_FORMAT, wd=None):
    fp = remove_protocol(file_path)
    path = fp if wd is None else os.path.join(wd,fp)
    dt = pytz.timezone('Europe/Vienna').localize(datetime.datetime.fromtimestamp(os.path.getctime(path)).replace(microsecond=0))
    return dt.strftime(fmt)

def main():
    print get_file_ctime_iso_date_str("./datetimeutils.py")
    print get_file_ctime_iso_date_str("./datetimeutils.py", "%d.%m.%Y %H:%M:%S")

if __name__ == "__main__":
    main()
