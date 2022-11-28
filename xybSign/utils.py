import datetime

import pytz


def get_beijing_time():
    return datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai'))
