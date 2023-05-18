import time
import datetime


def now() -> datetime.datetime:
    return datetime.datetime.now()


def today() -> datetime.datetime:
    return datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)


def days_ago(days: int) -> datetime.datetime:
    the_date = datetime.datetime.today() - datetime.timedelta(days=days)
    return the_date.replace(hour=0, minute=0, second=0, microsecond=0)


def days_after(days: int) -> datetime.datetime:
    the_date = datetime.datetime.today() + datetime.timedelta(days=days)
    return the_date.replace(hour=0, minute=0, second=0, microsecond=0)


def tomorrow() -> datetime.datetime:
    return days_after(1)


def yesterday() -> datetime.datetime:
    return days_ago(1)


def years_ago_of(base: datetime.datetime, years: int):
    the_date = base - datetime.timedelta(days=years*365)
    return the_date.replace(hour=0, minute=0, second=0, microsecond=0)


def years_ago(years: int) -> datetime.datetime:
    return years_ago_of(datetime.datetime.today(), years)


def tomorrow_of(_time: datetime.datetime):
    return _time + datetime.timedelta(days=1)


def yesterday_of(_time: datetime.datetime):
    return _time - datetime.timedelta(days=1)


def end_of_month(_time: datetime.datetime):
    if _time.month == 12:
        return _time.replace(day=31)
    return _time.replace(month=_time.month+1, day=1) - datetime.timedelta(days=1)


def to_date(_time: datetime.date or datetime.datetime or any):
    if type(_time) == datetime.date:
        return _time
    elif type(_time) == datetime.datetime:
        return _time.date()
    elif isinstance(_time, str):
        # TODO: str to datetime then to date
        pass
    else:
        # TODO: to py datetime then to date
        pass


def to_datetime(_date: datetime.date or datetime.datetime or any):
    if type(_date) == datetime.datetime:
        return _date
    elif type(_date) == datetime.date:
        return datetime.datetime.combine(_date, datetime.datetime.min.time())
    elif isinstance(_date, str):
        # TODO: str to datetime
        pass
    else:
        # TODO: to py datetime
        pass


# From https://stackoverflow.com/a/45292233

def quarter_head(dt=datetime.date.today()):
    return datetime.datetime(dt.year, (dt.month - 1) // 3 * 3 + 1, 1)


def quarter_tail(dt=datetime.date.today()) -> datetime.datetime:
    nextQtYr = dt.year + (1 if dt.month > 9 else 0)
    nextQtFirstMo = (dt.month - 1) // 3 * 3 + 4
    nextQtFirstMo = 1 if nextQtFirstMo==13 else nextQtFirstMo
    nextQtFirstDy = datetime.datetime(nextQtYr, nextQtFirstMo, 1)
    return nextQtFirstDy - datetime.timedelta(days=1)


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


def to_py_datetime(dt: any) -> datetime.datetime or None:
    if isinstance(dt, str):
        return text_auto_time(dt)

    if isinstance(dt, datetime.datetime):
        return dt
    if isinstance(dt, datetime.date):
        return datetime.datetime.combine(dt, datetime.min.time())

    # The float time stamp must be time.time()
    if isinstance(dt, float):
        return datetime.datetime.fromtimestamp(dt)

    # pyqt date and time
    from PyQt5.QtCore import QDate, QDateTime
    if isinstance(dt, QDate):
        return datetime.datetime.combine(dt.toPyDate(), datetime.min.time())
    if isinstance(dt, QDateTime):
        return dt.toPyDateTime()

    # DataFrame time
    import pandas as pd
    if isinstance(dt, pd.Timestamp):
        return dt.to_pydatetime()

    return None


def text_auto_time(text: str) -> datetime.datetime or None:
    if text is None:
        return None
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


def date2text(_time: datetime.datetime) -> str:
    return _time.strftime('%Y-%m-%d')


def datetime2text(_time: datetime.datetime) -> str:
    return _time.strftime('%Y-%m-%d %H:%M:%S')


def default_since() -> datetime.datetime:
    return text2date('1990-01-01')


def now_week_days() -> int:
    """
    Get week day of now.
    :return: Monday is 0 and Sunday is 6
    """
    return datetime.datetime.today().weekday()


def week_day_of(_time: datetime.date or datetime.datetime) -> int:
    """
    Get week day of the date you specified.
    :return: Monday is 0 and Sunday is 6
    """
    return _time.weekday()


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


class DelayerMinuteLimit(Delayer):
    """
    Use the class to create minute limitation delayer
    """
    def __init__(self, limit_per_min: int):
        delay = (60 * 1000 // limit_per_min) if limit_per_min > 0 else 0
        super(DelayerMinuteLimit, self).__init__(delay)


# -------------------------------------------------- DateTimeIterator --------------------------------------------------

class DateTimeIterator:
    """
    Iterate datetime range or datetime days.
    """
    def __init__(self, since: datetime.datetime, until: datetime.datetime):
        """
        Specify iterate datetime range.
        :param since: The start datetime
        :param until: The end datetime
        """
        self.__since = since
        self.__until = until
        self.__iter_from = self.__since
        self.__iter_to = self.__since
        self.__first_iter = True

    def end(self) -> bool:
        """
        Check whether the iteration ends.
        :return: True if ends else False
        """
        return self.__iter_to >= self.__until

    def data_range(self) -> (datetime.datetime, datetime.datetime):
        """
        Get current iteration range. For single days iteration, the from and to are the same value.
        :return: Current iteration range as (datetime.datetime, datetime.datetime)
        """
        return self.__iter_from, self.__iter_to

    # ------------------------- Regular iteration -------------------------

    def iter_days(self, days: int) -> (datetime.datetime, datetime.datetime):
        """
        Iterate datetime range by days.
        :param days: The iteration step by days.
        :return: The iteration range after this iteration as (datetime.datetime, datetime.datetime)
        """
        return self.iter_delta(datetime.timedelta(days=days))

    def iter_years(self, years: int) -> (datetime.datetime, datetime.datetime):
        """
        Iterate datetime range by years.
        :param years: The iteration step by years.
        :return: The iteration range after this iteration as (datetime.datetime, datetime.datetime)
        """
        return self.iter_delta(datetime.timedelta(days=years*365))

    def iter_delta(self, delta: datetime.timedelta) -> (datetime.datetime, datetime.datetime):
        """
        Iterate datetime range by datetime delta.
        :param delta: The iteration step by datetime delta.
        :return: The iteration range after this iteration as (datetime.datetime, datetime.datetime)
        """
        self.__iter_from = self.__iter_to
        self.__iter_to += delta
        if self.end():
            self.__iter_to = self.__until
        self.__first_iter = False
        return self.data_range()

    # ------------------------ Irregular iteration ------------------------

    def iter_year_tail(self):
        """
        Iterate the year tail days.
        :return: The iteration day after this iteration, the 2 values in this tuple are the same.
        """
        if not self.end():
            if self.__first_iter:
                year = self.__iter_from.year
            else:
                year = self.__iter_from.year + 1
            self.__iter_from = datetime.datetime(year=year, month=12, day=31, hour=0, minute=0, second=0)
            self.__iter_to = self.__iter_from
            self.__first_iter = False
        return self.data_range()

    def iter_quarter_tail(self):
        """
        Iterate the quarter tail days.
        :return: The iteration day after this iteration, the 2 values in this tuple are the same.
        """
        if not self.end():
            if self.__first_iter:
                self.__iter_from = quarter_tail(self.__iter_from)
            else:
                self.__iter_from = quarter_tail(self.__iter_from + datetime.timedelta(days=1))
            self.__iter_to = self.__iter_from
            self.__first_iter = False
        return self.data_range()


# ----------------------------------------------------------------------------------------------------------------------

def test_datetime_iterator_quarter_tail():
    days = []
    iter = DateTimeIterator(datetime.datetime(2000, 3, 31),
                            datetime.datetime(2000, 9, 30))
    while not iter.end():
        days.append(iter.iter_quarter_tail()[0])
    print(days)
    assert days == [datetime.datetime(2000, 3, 31), datetime.datetime(2000, 6, 30), datetime.datetime(2000, 9, 30)]

    days = []
    iter = DateTimeIterator(datetime.datetime(2000, 4, 1),
                            datetime.datetime(2000, 10, 1))
    while not iter.end():
        days.append(iter.iter_quarter_tail()[0])
    print(days)
    assert days == [datetime.datetime(2000, 6, 30), datetime.datetime(2000, 9, 30), datetime.datetime(2000, 12, 31)]


def main():
    test_datetime_iterator_quarter_tail()


# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(e)
        print(traceback.format_exc())
        exit(1)
    finally:
        pass













