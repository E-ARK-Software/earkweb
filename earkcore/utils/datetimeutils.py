import os
import time
import datetime
from pytz import timezone
from earkcore.utils.fileutils import remove_protocol
from functools import wraps

DT_ISO_FORMAT = '%Y-%m-%dT%H:%M:%S%z'

DT_ISO_FMT_SEC_PREC = '%Y-%m-%dT%H:%M:%S'

TS_FORMAT = '%Y-%m-%d %H:%M:%S'

EU_UI_FORMAT = '%d.%m.%Y %H:%M:%S'

TASK_EXEC_TIMES = {}


def reformat_date_string(origin_fmt, origin_dts, target_fmt):
    return datetime.datetime.strptime(origin_dts, origin_fmt).strftime(target_fmt)


def get_file_ctime_iso_date_str(file_path, fmt=DT_ISO_FORMAT, wd=None):
    fp = remove_protocol(file_path)
    path = fp if wd is None else os.path.join(wd, fp)
    dt = timezone('Europe/Vienna').localize(datetime.datetime.fromtimestamp(os.path.getctime(path)).replace(microsecond=0))
    return dt.strftime(fmt)


def ts_date(fmt=TS_FORMAT):
    return datetime.datetime.fromtimestamp(time.time()).strftime(fmt)


def current_timestamp(fmt=DT_ISO_FMT_SEC_PREC):
    # naive_now = datetime.datetime.utcnow()
    # utc_now = naive_now.replace(tzinfo=pytz.utc)
    # tz = pytz.timezone('Europe/Vienna')
    # local_now = utc_now.replace(tzinfo=pytz.utc).astimezone(tz)
    dt = datetime.datetime.now(tz=timezone('Europe/Vienna'))
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


class LengthBasedDateFormat(object):
    date_str = None

    def __init__(self, date_str):
        self.date_str = date_str

    def reformat(self, target_fmt='%Y-%m-%dT%H:%M:%SZ'):
        method_name = 'format_' + str(len(self.date_str))
        method = getattr(self, method_name, lambda: "1970-01-01T00:00:00Z")
        return method(target_fmt)

    def format_4(self, target_fmt):
        return reformat_date_string("%Y", self.date_str, target_fmt)

    def format_6(self, target_fmt):
        return reformat_date_string("%d%m%Y", self.date_str, target_fmt)

    def format_10(self, target_fmt):
        return reformat_date_string("%d.%m.%Y", self.date_str, target_fmt)


def main():
    print get_file_ctime_iso_date_str("./datetimeutils.py")
    print get_file_ctime_iso_date_str("./datetimeutils.py", "%d.%m.%Y %H:%M:%S")
    print ts_date()

    @measuretime
    def to_be_measured(param):
        for i in range(0, param, 1):
            time.sleep(1)
            print i
        return True

    to_be_measured(5)
    print 'Execution time max: %d seconds' % (TASK_EXEC_TIMES['id'])
    lbdf = LengthBasedDateFormat("2015")
    print lbdf.reformat()


if __name__ == "__main__":
    main()
