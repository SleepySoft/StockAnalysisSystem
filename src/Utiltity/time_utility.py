import datetime
import time


def now() -> datetime.datetime:
    return datetime.datetime.now()


def today() -> datetime.datetime:
    date_text = datetime.datetime.today().strftime('%Y-%m-%d')
    return text2date(date_text)


def tomorrow() -> datetime.datetime:
    date_text = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    return text2date(date_text)


def yesterday() -> datetime.datetime:
    date_text = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    return text2date(date_text)


def days_ago(days: int) -> datetime.datetime:
    now_date = datetime.datetime.today()
    now_date -= datetime.timedelta(days=days)
    date_text = now_date.strftime('%Y-%m-%d')
    return text2date(date_text)


def years_ago(years: int) -> datetime.datetime:
    return years_ago_of(datetime.datetime.today(), years)


def years_ago_of(base: datetime.datetime, years: int):
    date = base - datetime.timedelta(days=years*365)
    date_text = date.strftime('%Y-%m-%d')
    return text2date(date_text)


def tomorrow_of(time: datetime.datetime):
    return time + datetime.timedelta(days=1)


def yesterday_of(time: datetime.datetime):
    return time - datetime.timedelta(days=1)


def date2datetime(d: datetime.date) -> datetime.datetime:
    return datetime.datetime(year=d.year, month=d.month, day=d.day)


# From https://stackoverflow.com/a/16864368/12929244

def previous_quarter(reference_date) -> datetime.datetime:
    if reference_date.month < 4:
        return datetime.datetime(reference_date.year - 1, 12, 31, 0, 0, 0)
    elif reference_date.month < 7:
        return datetime.datetime(reference_date.year, 3, 31, 0, 0, 0)
    elif reference_date.month < 10:
        return datetime.datetime(reference_date.year, 6, 30, 0, 0, 0)
    else:
        return datetime.datetime(reference_date.year, 9, 30, 0, 0, 0)


def text_auto_time(text: str) -> datetime.datetime:
    if isinstance(text, datetime.datetime):
        return text
    # noinspection PyBroadException
    try:
        return datetime.datetime.strptime(text, '%Y-%m-%d %H:%M:%S')
    except Exception:
        pass
    # noinspection PyBroadException
    try:
        return datetime.datetime.strptime(text, '%Y-%m-%d')
    except Exception:
        pass
    # noinspection PyBroadException
    try:
        return datetime.datetime.strptime(text, '%H:%M:%S')
    except Exception:
        pass
    # noinspection PyBroadException
    try:
        return datetime.datetime.strptime(text, '%Y%m%d')
    except Exception:
        pass
    return None


def text2date(text: str) -> datetime.datetime:
    return datetime.datetime.strptime(text, '%Y-%m-%d')


def text2datetime(text: str) -> datetime.datetime:
    return datetime.datetime.strptime(text, '%Y-%m-%d %H:%M:%S')


def date2text(time: datetime.datetime) -> str:
    return time.strftime('%Y-%m-%d')


def datetime2text(time: datetime.datetime) -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S')


def default_since() -> datetime.datetime:
    return text2date('1990-01-01')


def normalize_time_serial(time_serial: tuple or list,
                          since_default: datetime.datetime = None,
                          until_default: datetime.datetime = None) -> (datetime.datetime, datetime.datetime):
    since = time_serial[0] if time_serial is not None and \
                              isinstance(time_serial, (list, tuple)) and len(time_serial) > 0 else since_default
    until = time_serial[1] if time_serial is not None and \
                              isinstance(time_serial, (list, tuple)) and len(time_serial) > 1 else until_default
    if since is not None and not isinstance(since, datetime.datetime):
        since = text_auto_time(str(since))
    if until is not None and not isinstance(until, datetime.datetime):
        until = text_auto_time(str(until))
    return since, until


# ------------------------------------------------------- Clock --------------------------------------------------------

class Clock:
    def __init__(self, start_flag: bool = True):
        self.__start_time = time.time()
        self.__start_flag = start_flag
        self.__freeze_time = None

    def reset(self):
        self.__start_flag = True
        self.__freeze_time = None
        self.__start_time = time.time()

    def freeze(self):
        self.__freeze_time = time.time()

    def elapsed(self) -> float:
        if self.__freeze_time is None:
            base_time = time.time()
        else:
            base_time = self.__freeze_time
        return (base_time - self.__start_time) if self.__start_flag else 0

    def elapsed_s(self) -> int:
        return int(self.elapsed()) if self.__start_flag else 0

    def elapsed_ms(self) -> int:
        return int(self.elapsed() * 1000) if self.__start_flag else 0


# ------------------------------------------------------ Delayer -------------------------------------------------------

class Delayer:
    def __init__(self, delay_ms: int):
        self.__delay = delay_ms
        self.__clock = Clock()

    def reset(self):
        self.__clock.reset()

    def delay(self):
        elapsed = self.__clock.elapsed()
        if elapsed < self.__delay / 1000:
            delay_s = self.__delay / 1000 - elapsed
            time.sleep(delay_s)
            print('Delay %s ms' % (delay_s * 1000))
        self.__clock.reset()


# -------------------------------------------------- DateTimeIterator --------------------------------------------------

class DateTimeIterator:
    def __init__(self, since: datetime.datetime, until: datetime.datetime):
        self.__since = since
        self.__until = until
        self.__iter_from = self.__since
        self.__iter_to = self.__since

    def end(self) -> bool:
        return self.__iter_to >= self.__until

    def data_range(self) -> (datetime.datetime, datetime.datetime):
        return self.__iter_from, self.__iter_to

    def iter_days(self, days: int) -> (datetime.datetime, datetime.datetime):
        return self.iter_delta(datetime.timedelta(days=days))

    def iter_years(self, years: int) -> (datetime.datetime, datetime.datetime):
        return self.iter_delta(datetime.timedelta(days=years*365))

    def iter_delta(self, delta: datetime.timedelta) -> (datetime.datetime, datetime.datetime):
        self.__iter_from = self.__iter_to
        self.__iter_to += delta
        if self.end():
            self.__iter_to = self.__until
        return self.data_range()














