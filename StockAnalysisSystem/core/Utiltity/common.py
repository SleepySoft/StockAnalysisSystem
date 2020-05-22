import string
import logging
import sys
import collections

import requests
import traceback
import threading
import numpy as np
import pandas as pd
from io import BytesIO
from bs4 import BeautifulSoup
from datetime import time, datetime


# -----------------------------------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s.%(msecs)03d] [ %(levelname)6s ] --- %(message)-200s | (%(filename)s:%(lineno)s)',
    datefmt='%m-%d %H:%M',
    # filename='/tmp/myapp.log',
    # filemode='w'
)

# # 定义日志处理器将INFO或者以上级别的日志发送到 sys.stderr
# console = logging.StreamHandler()
# console.setLevel(logging.INFO)
#
# # 设置控制台日志的格式
# formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# console.setFormatter(formatter)
#
# logging.getLogger('').addHandler(console)


# -----------------------------------------------------------------------------------------------------

def nop(*args):
    pass


def slog(*args):
    print(''.join([str(arg) for arg in args]))


def log_dbg(*args):
    print(''.join([str(arg) for arg in args]))


def log_info(*args):
    print(''.join([str(arg) for arg in args]))


def log_error(*args):
    print(''.join([str(arg) for arg in args]))


# ---------------------------------------------------- Progress Rate ---------------------------------------------------

class ProgressRate:
    INDEX_CURRENT_PROGRESS = 0
    INDEX_TOTAL_PROGRESS = 1

    def __init__(self):
        self.__progress_table = collections.OrderedDict()

    def reset(self):
        self.__progress_table.clear()

    def combine_with(self, progress_rate):
        self.__progress_table.update(progress_rate.get_progress_table())

    def has_progress(self, identity: str or [str]):
        key = self.normalize_identity(identity)
        return key in self.__progress_table.keys()

    def get_progress_table(self) -> collections.OrderedDict:
        return self.__progress_table

    def get_progress_identities(self) -> []:
        return list(self.__progress_table.keys())

    def increase_progress(self, identity: str or [str], inc: int = 1):
        key = self.normalize_identity(identity)
        if key in self.__progress_table.keys():
            current = self.__progress_table[key][ProgressRate.INDEX_CURRENT_PROGRESS]
            if current is not None:
                self.__progress_table[key][ProgressRate.INDEX_CURRENT_PROGRESS] = current + inc

    def set_progress(self, identity: str or [str], current: int or None, total: int or None):
        key = self.normalize_identity(identity)
        if key not in self.__progress_table.keys():
            self.__progress_table[key] = [0, 1]
        if current is not None:
            self.__progress_table[key][ProgressRate.INDEX_CURRENT_PROGRESS] = current
        if total is not None:
            self.__progress_table[key][ProgressRate.INDEX_TOTAL_PROGRESS] = total

    def get_progress(self, identity: str) -> (int, int):
        key = self.normalize_identity(identity)
        return self.__progress_table.get(key, (0, 1))

    def get_progress_rate(self, identity: str or [str]) -> float:
        key = self.normalize_identity(identity)
        if key in self.__progress_table.keys():
            total = self.__progress_table[key][ProgressRate.INDEX_TOTAL_PROGRESS]
            current = self.__progress_table[key][ProgressRate.INDEX_CURRENT_PROGRESS]
        else:
            total = 1
            current = 0
        current = min(current, total)
        return 1 if total == 0 else current / total

    def normalize_identity(self, identity: str or list) -> str:
        return '.'.join(list(identity)) if isinstance(identity, (list, tuple)) else identity


# ------------------------------------------------------ Singleton -----------------------------------------------------

# Based on tornado.ioloop.IOLoop.instance() approach.
# See https://github.com/facebook/tornado
# Whole idea for this metaclass is taken from: https://stackoverflow.com/a/6798042/2402281
class ThreadSafeSingleton(type):
    _instances = {}
    _singleton_lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        # double-checked locking pattern (https://en.wikipedia.org/wiki/Double-checked_locking)
        if cls not in cls._instances:
            with cls._singleton_lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(ThreadSafeSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

# class YourImplementation(metaclass=ThreadSafeSingleton):
#     def __init__(self, *args, **kwargs):
#         pass  # your implementation goes here


# -------------------------------------------- Web related --------------------------------------------

def Download(url: str) -> bytes or None:
    try:
        r = requests.get(url)
        return r.content
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        return None
    finally:
        pass
    return None


def DownloadText(url: str, decode='gb2312') -> str:
    c = Download(url)
    if c is not None:
        return c.decode(decode)
    return ''


def DownloadCsvAsDF(url, decode='gb2312') -> pd.DataFrame:
    content = Download(url)
    return pd.read_csv(BytesIO(content), header=None, encoding=decode)


def GetWebAsSoap(url, decode='gb2312'):
    content = DownloadText(url, decode)
    return BeautifulSoup(content, "html.parser")


# -------------------------------------------- XML parse --------------------------------------------

# chain: [(tag, {properties}), ...]
def ChainParse(root, chain, find_list: []):
    if len(chain) == 0:
        return
    tag, properties = chain[0]
    childs = root.find_all(tag, properties)  # , recursive=(len(properties) > 0)
    if len(chain) == 1:
        find_list.extend(childs)
    else:
        for child in childs:
            ChainParse(child, chain[1:], find_list)


# -------------------------------------------- Type parse --------------------------------------------

def str2int_safe(text: str, default=0, base=10) -> float:
    try:
        return int(text, base)
    except Exception as e:
        return default
    finally:
        pass


def str2float_safe(text: str, default=0.0) -> float:
    try:
        return float(text)
    except Exception as e:
        return default
    finally:
        pass


def str_is_float(text: str) -> bool:
    try:
        float(text)
        return True
    except Exception as e:
        return False
    finally:
        pass


def do_limitation(number: int, minimal: int, maximum: int) -> int:
    num = max(number, min(minimal, maximum))
    num = min(num, max(minimal, maximum))
    return num


def correct_start_end(start: int, end: int) -> tuple:
    _start = min(start, end)
    _end = max(start, end)
    return _start, _end


def correct_start_end(start: int, end: int, start_limit: int, end_limit: int) -> tuple:
    _start = min(start, end)
    _end = max(start, end)
    _start = do_limitation(_start, start_limit, end_limit)
    _end = do_limitation(_end, start_limit, end_limit)
    return _start, _end


def str_available(value: str) -> bool:
    return value is not None and isinstance(value, str) and value != ''


# -------------------------------------------- DataFrame operation --------------------------------------------

def ClipDataFrame(df: pd.DataFrame, index: [int], columns: [str]):
    df_sub = pd.DataFrame()
    for c in columns:
        if c not in df.columns:
            serial = np.empty(df.shape[0])
            serial.fill(np.nan)
        else:
            serial = df[c]
        df_sub.insert(len(df_sub.columns), c, serial)
    return df_sub.loc[index]


def MergeDataFrameOnIndex(df_l: pd.DataFrame, df_r: pd.DataFrame):
    if df_l is None:
        return df_r
    if df_r is None:
        return df_l
    return pd.merge(df_l, df_r, left_index=True, right_index=True, how='outer')


def MergeDataFrameOnColumn(df_l: pd.DataFrame, df_r: pd.DataFrame, on_col: str):
    if df_l is None or on_col not in df_l.columns:
        return df_r
    if df_r is None or on_col not in df_r.columns:
        return df_l
    return pd.merge(df_l, df_r, on=on_col, how='outer')


# return (copied, uncopied)
def DataFrameColumnCopy(df_from: pd.DataFrame, df_to: pd.DataFrame, columns: [str]) -> (int, int):
    copied = uncopied = 0
    for c in columns:
        if c not in df_from.columns.tolist():
            uncopied += 1
            continue
        col = df_from[c]
        if c not in df_to.columns.tolist():
            df_to.insert(len(df_to.columns), c, col.copy())
        else:
            df_to[c] = col.copy()
        copied += 1
    return copied, uncopied


# -------------------------------------------- Date/Time --------------------------------------------


# Parse ####-##-## format date
# Return (year, month, day)
def str_to_date(text: str) -> tuple:
    splited = text.split('-')
    while len(splited) < 3:
        splited.append('0')
    return tuple([str2int_safe(s) for s in splited])


# ms in float format
def TickCount() -> float:
    return time.clock()


def Date() -> tuple:
    dt = datetime.now()
    return dt.year, dt.month, dt.day


def Time() -> tuple:
    dt = datetime.now()
    return dt.hour, dt.minute, dt.second


def DateTimeString() -> str:
    return datetime.now().isoformat()


# -------------------------------------------- Sort algorithm --------------------------------------------

def topological_sort(source):
    """perform topo sort on elements.

    :arg source: list of ``(name, [list of dependancies])`` pairs
    :returns: list of names, with dependancies listed first
    """
    pending = [(name, set(deps)) for name, deps in source] # copy deps so we can modify set in-place
    emitted = []
    while pending:
        next_pending = []
        next_emitted = []
        for entry in pending:
            name, deps = entry
            deps.difference_update(emitted) # remove deps we emitted last pass
            if deps: # still has deps? recheck during next pass
                next_pending.append(entry)
            else: # no more deps? time to emit
                yield name
                emitted.append(name) # <-- not required, but helps preserve original ordering
                next_emitted.append(name) # remember what we emitted for difference_update() in next pass
        if not next_emitted: # all entries have unmet deps, one of two things is wrong...
            raise ValueError("cyclic or missing dependancy detected: %r" % (next_pending,))
        pending = next_pending
        emitted = next_emitted


# -------------------------------------------- set --------------------------------------------


def set_missing(set_test, set_base) -> list:
    set1, set2 = set(set_test), set(set_base)
    return [i for i in set1 if i not in set2]


# -------------------------------------------- Stock related --------------------------------------------

def get_stock_exchange(stock_code: str) -> str:
    """
    Get the stock market according to the code rule.
    :param stock_code: The stock code that need to check/
    :return: Exchange. SSE - Shanghai, SZSE - Shenzhen. Empty string if not recognized.
    """
    if len(stock_code) != 6:
        return ''
    if stock_code.startswith('000') or stock_code.startswith('300') \
            or stock_code.startswith('200')or stock_code.startswith('002'):
        # 000: 普通
        # 300: 创业板
        # 200: B股
        # 002: 中小板
        return 'SZSE'
    if stock_code.startswith('60') or stock_code.startswith('688') or stock_code.startswith('900'):
        # 600, 601, 603: 普通
        # 688: 科创板
        # 900: B股
        return 'SSE'
    return ''


def stock_code_to_stock_identity(stock_code: str) -> str:
    exchange = get_stock_exchange(stock_code)
    return stock_code + '.' + exchange if exchange != '' else ''


def normalize_stock_identity(stock_code: str) -> str:
    if stock_code.endswith('.SSE') or stock_code.endswith('.SZSE'):
        return stock_code
    return stock_code_to_stock_identity(stock_code)


def index_to_excel_column_name(index: int) -> str:
    index = int(index)
    column_index = ''
    while index > 0:
        remainder = (index - 1) % 26 + 1
        column_index += string.ascii_uppercase[remainder - 1]
        index -= remainder
        index //= 26
    return column_index[::-1]


# ----------------------------------------------------------------------------------------------------------------------


def test_index_to_excel_column_name():
    assert index_to_excel_column_name(1) == 'A'
    assert index_to_excel_column_name(2) == 'B'
    assert index_to_excel_column_name(25) == 'Y'
    assert index_to_excel_column_name(26) == 'Z'

    assert index_to_excel_column_name(27) == 'AA'
    assert index_to_excel_column_name(52) == 'AZ'
    assert index_to_excel_column_name(53) == 'BA'
    assert index_to_excel_column_name(78) == 'BZ'
    assert index_to_excel_column_name(702) == 'ZZ'

    assert index_to_excel_column_name(703) == 'AAA'

    for i in range(1, 10000):
        print(str(i) + ' -> ' + index_to_excel_column_name(i))


def test_entry():
    test_index_to_excel_column_name()


def main():
    test_entry()
    print('All Test Passed.')


# ----------------------------------------------------------------------------------------------------------------------

def exception_hook(type, value, tback):
    # log the exception here
    print('Exception hook triggered.')
    print(type)
    print(value)
    print(tback)
    # then call the default handler
    sys.__excepthook__(type, value, tback)


if __name__ == "__main__":
    sys.excepthook = exception_hook
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass

















