import os
import pytz, time, datetime
from earkcore.utils.fileutils import remove_protocol
from functools import wraps

DT_ISO_FORMAT='%Y-%m-%dT%H:%M:%S%z'

DT_ISO_FMT_SEC_PREC='%Y-%m-%dT%H:%M:%S'

TS_FORMAT='%Y-%m-%d %H:%M:%S'

TASK_EXEC_TIMES = {}

def get_file_ctime_iso_date_str(file_path, fmt=DT_ISO_FORMAT, wd=None):
    fp = remove_protocol(file_path)
    path = fp if wd is None else os.path.join(wd,fp)
    dt = pytz.timezone('Europe/Vienna').localize(datetime.datetime.fromtimestamp(os.path.getctime(path)).replace(microsecond=0))
    return dt.strftime(fmt)

def ts_date(fmt = TS_FORMAT):
    return datetime.datetime.fromtimestamp(time.time()).strftime(fmt)

def current_timestamp(fmt = DT_ISO_FMT_SEC_PREC):
    # naive_now = datetime.datetime.utcnow()
    # utc_now = naive_now.replace(tzinfo=pytz.utc)
    # tz = pytz.timezone('Europe/Vienna')
    # local_now = utc_now.replace(tzinfo=pytz.utc).astimezone(tz)
    dt = datetime.datetime.now(tz=pytz.timezone('Europe/Vienna'))
    return dt.strftime(fmt)

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
