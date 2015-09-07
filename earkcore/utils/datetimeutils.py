import os
import pytz, time, datetime
from earkcore.utils.fileutils import remove_protocol
from functools import wraps

DT_ISO_FORMAT='%Y-%m-%dT%H:%M:%S%z'

TS_FORMAT='%Y-%m-%d %H:%M:%S'

TASK_EXEC_TIMES = {}

def get_file_ctime_iso_date_str(file_path, fmt=DT_ISO_FORMAT, wd=None):
    fp = remove_protocol(file_path)
    path = fp if wd is None else os.path.join(wd,fp)
    dt = pytz.timezone('Europe/Vienna').localize(datetime.datetime.fromtimestamp(os.path.getctime(path)).replace(microsecond=0))
    return dt.strftime(fmt)

def ts_date():
    return datetime.datetime.fromtimestamp(time.time()).strftime(TS_FORMAT)

def measuretime(fn):
    @wraps(fn)
    def measuring(*args, **kwargs):
        start_time = time.time()
        ret = fn(*args, **kwargs)
        elapsed_time = time.time() - start_time
        TASK_EXEC_TIMES["id"] = elapsed_time
        return ret
    return measuring

def main():
    print get_file_ctime_iso_date_str("./datetimeutils.py")
    print get_file_ctime_iso_date_str("./datetimeutils.py", "%d.%m.%Y %H:%M:%S")
    print ts_date()

    @measuretime
    def to_be_measured(param):
        for i in range(0, param, 1):
            time.sleep( 1 )
            print i
        return True
    to_be_measured(5)
    print 'Execution time max: %d seconds' % (TASK_EXEC_TIMES['id'])

if __name__ == "__main__":
    main()
