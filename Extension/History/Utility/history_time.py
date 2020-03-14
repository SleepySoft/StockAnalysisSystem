import re
import math
import time
import traceback
from os import sys, path

root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Utility.to_arab import *
    from Utility.history_public import *
except Exception as e:
    sys.path.append(root_path)
    from Utility.to_arab import *
    from Utility.history_public import *
finally:
    pass


def now_cn_str() -> str:
    return time.strftime('%Y{y}%m{m}%d{d}').format(y='年', m='月', d='日')

# TODO: Use NLP to process nature language


class HistoryTime:

    TICK = int
    TICK_SEC = 1
    TICK_MIN = TICK_SEC * 60
    TICK_HOUR = TICK_MIN * 60
    TICK_DAY = TICK_HOUR * 24
    TICK_YEAR = TICK_DAY * 366
    TICK_WEEK = TICK(TICK_YEAR / 52)
    TICK_MONTH = [1,
                  31 * TICK_DAY, 60 * TICK_DAY, 91 * TICK_DAY, 121 * TICK_DAY,
                  152 * TICK_DAY, 182 * TICK_DAY, 213 * TICK_DAY, 244 * TICK_DAY,
                  274 * TICK_DAY, 304 * TICK_DAY, 335 * TICK_DAY, 366 * TICK_DAY]

    EFFECTIVE_TIME_DIGIT = 10

    YEAR_FINDER = re.compile(r'(\d+年)')
    MONTH_FINDER = re.compile(r'(\d+月)')
    DAY_FINDER = re.compile(r'(\d+日)')

    # ------------------------------------------------------------------------

    SEPARATOR = [
        ',',
        '~',
        '～',
        '-',
        '–',
        '－',
        '—',
        '―',
        '─',
        '至',
        '到',
    ]

    SPACE_CHAR = [
        '约',
    ]

    REPLACE_CHAR = [
        ('元月', '1月'),
        ('正月', '1月'),
        ('世纪', '00'),
        ('至今', now_cn_str()),
    ]

    PREFIX_CE = [
        'ac',
        'ce',
        'common era',
        '公元',
    ]

    PREFIX_BCE = [
        'bc',
        'bce',
        'before common era',
        '公元前',
        '前',
        '距今',
        '史前',
    ]

    def __init__(self):
        print("Create HistoryTime instance is not necessary.")

    @staticmethod
    def now_tick() -> TICK:
        return HistoryTime.pytime_to_tick(time.localtime(time.time()))

    # ------------------------------- Constant -------------------------------

    @staticmethod
    def year(year: int = 1) -> TICK:
        return year * HistoryTime.TICK_YEAR

    @staticmethod
    def month(month: int = 1) -> TICK:
        month = max(month, 1)
        month = min(month, 12)
        return HistoryTime.TICK_MONTH[month - 1]

    @staticmethod
    def week(week: int = 1) -> TICK:
        return int(week * HistoryTime.TICK_WEEK)

    @staticmethod
    def day(day: int = 1) -> TICK:
        return int(day * HistoryTime.TICK_DAY)

    # ------------------------------- Convert -------------------------------

    @staticmethod
    def pytime_to_tick(ts: time.struct_time) -> TICK:
        return HistoryTime.build_history_time_tick(ts.tm_year, ts.tm_mon, ts.tm_mday,
                                                   ts.tm_hour, ts.tm_min, ts.tm_sec)

    @staticmethod
    def year_of_tick(tick: TICK) -> int:
        return HistoryTime.date_of_tick(tick)[0]

    @staticmethod
    def month_of_tick(tick: TICK) -> int:
        return HistoryTime.date_of_tick(tick)[1]

    @staticmethod
    def day_of_tick(tick: TICK) -> int:
        return HistoryTime.date_of_tick(tick)[2]

    @staticmethod
    def date_of_tick(tick: TICK) -> (int, int, int):
        sign = 1 if tick >= 0 else -1
        day = 0
        year = sign * int(abs(tick) / HistoryTime.TICK_YEAR)
        month = 12
        year_mod = abs(tick) % HistoryTime.TICK_YEAR
        for i in range(0, len(HistoryTime.TICK_MONTH)):
            if year_mod <= HistoryTime.TICK_MONTH[i]:
                day_tick = year_mod if i == 0 else year_mod - HistoryTime.TICK_MONTH[i - 1]
                day = day_tick / HistoryTime.day()
                month = i + 1
                break
        return int(year), int(month), int(day)

    @staticmethod
    def decimal_year_to_tick(year: float) -> TICK:
        return int(year * HistoryTime.TICK_YEAR)

    @staticmethod
    def tick_to_decimal_year(tick: TICK) -> float:
        return HistoryTime.round_decimal_year(float(tick) / HistoryTime.TICK_YEAR)

    @staticmethod
    def tick_to_standard_string(tick: TICK, show_date: bool = False, show_time: bool = False) -> str:
        year, month, day = HistoryTime.date_of_tick(tick)
        if year < 0:
            text = str(-year) + ' BCE'
        else:
            text = str(year) + ' CE'
        if show_date:
            text += ' ' + str(month) + '/' + str(day)
        if show_time:
            pass
        return text

    # ------------------------------- Calculation -------------------------------

    @staticmethod
    def round_decimal_year(year: float):
        return round(year, HistoryTime.EFFECTIVE_TIME_DIGIT)

    @staticmethod
    def decimal_year_equal(digital1: float, digital2: float):
        return abs(digital1 - digital2) < pow(1.0, -(HistoryTime.EFFECTIVE_TIME_DIGIT + 1))

    @staticmethod
    def build_history_time_tick(year: int = 0, month: int = 0, day: int = 0,
                                hour: int = 0, minute: int = 0, second: int = 0,
                                week: int = 0) -> TICK:
        sign = 1 if year >= 0 else -1
        tick = HistoryTime.year(abs(year)) + HistoryTime.month(month) + HistoryTime.day(day) + \
            hour * HistoryTime.TICK_HOUR + minute * HistoryTime.TICK_MIN + second * HistoryTime.TICK_MIN + \
            week * HistoryTime.TICK_WEEK
        return sign * tick

    # ------------------------------------------------------------------------

    @staticmethod
    def __get_first_item_except(items: list, expect: str):
        return items[0].replace(expect, '') if len(items) > 0 else ''

    @staticmethod
    def time_str_to_history_time(time_str: str) -> TICK:
        if str_includes(time_str.lower().strip(), HistoryTime.PREFIX_BCE):
            sign = -1
        else:
            sign = 1
        arablized_str = text_cn_num_to_arab(time_str)
        day = HistoryTime.__get_first_item_except(HistoryTime.DAY_FINDER.findall(arablized_str), '日')
        year = HistoryTime.__get_first_item_except(HistoryTime.YEAR_FINDER.findall(arablized_str), '年')
        month = HistoryTime.__get_first_item_except(HistoryTime.MONTH_FINDER.findall(arablized_str), '月')

        if year == '':
            number_str = int("".join(filter(str.isdigit, arablized_str)))
            return HistoryTime.build_history_time_tick(sign * int(number_str))
        else:
            return HistoryTime.build_history_time_tick(sign * str_to_int(year), str_to_int(month), str_to_int(day))

    @staticmethod
    def time_text_to_history_times(text: str) -> [TICK]:
        time_text_list = HistoryTime.split_normalize_time_text(text)
        return [HistoryTime.time_str_to_history_time(time_text) for time_text in time_text_list]

    @staticmethod
    def split_normalize_time_text(text: str) -> [str]:
        unified_time_str = text
        for space in HistoryTime.SPACE_CHAR:
            unified_time_str = unified_time_str.replace(space, '')

        for old_char, new_char in HistoryTime.REPLACE_CHAR:
            unified_time_str = unified_time_str.replace(old_char, new_char)

        for i in range(1, len(HistoryTime.SEPARATOR)):
            unified_time_str = unified_time_str.replace(HistoryTime.SEPARATOR[i], HistoryTime.SEPARATOR[0])

        time_str_list = unified_time_str.split(HistoryTime.SEPARATOR[0])
        time_str_list = [time_str.strip() for time_str in time_str_list if time_str.strip() != '']

        return time_str_list

    # ------------------------------------------------------------------------

    @staticmethod
    def standardize(time_str: str) -> ([float], [str]):
        unified_time_str = time_str

        for space in HistoryTime.SPACE_CHAR:
            unified_time_str = unified_time_str.replace(space, '')

        for old_char, new_char in HistoryTime.REPLACE_CHAR:
            unified_time_str = unified_time_str.replace(old_char, new_char)

        for i in range(1, len(HistoryTime.SEPARATOR)):
            unified_time_str = unified_time_str.replace(HistoryTime.SEPARATOR[i], HistoryTime.SEPARATOR[0])

        time_list = []
        error_list = []
        sub_time_str_list = unified_time_str.split(HistoryTime.SEPARATOR[0])
        for sub_time_str in sub_time_str_list:
            try:
                num = HistoryTime.parse_single_time_str(sub_time_str.strip())
                time_list.append(num)
            except Exception as e:
                error_list.append(sub_time_str)
                print('Parse time error: ' + sub_time_str + ' -> ' + str(e))
            finally:
                pass
        return time_list, error_list

    @staticmethod
    def parse_single_time_str(time_str: str) -> float:
        if time_str.lower().startswith(tuple(HistoryTime.PREFIX_BCE)):
            sign = -1
        elif time_str.lower().startswith(tuple(HistoryTime.PREFIX_CE)):
            sign = 1
        else:
            sign = 1
        # non_numeric_chars = ''.join(set(string.printable) - set(string.digits))
        if '年' in time_str:
            time_str = time_str[0: time_str.find('年')]
        number_str = int("".join(filter(str.isdigit, time_str)))
        # number_str = time_str.translate(non_numeric_chars)
        return sign * float(number_str)

    @staticmethod
    def standard_time_to_str(std_time: float) -> str:
        year = math.floor(std_time)
        date = std_time - year
        text = str(year)
        if std_time < 0:
            text = str(-year) + ' BCE'
        else:
            text = str(year) + ' CE'
        return text

    @staticmethod
    def tick_to_cn_date_text(his_tick: TICK) -> str:
        year = HistoryTime.year_of_tick(his_tick)
        month = HistoryTime.month_of_tick(his_tick)
        day = HistoryTime.day_of_tick(his_tick)
        if year < 0:
            text = '公元前' + str(-year) + '年'
        else:
            text = '公元' + str(-year) + '年'
        return text + str(month) + '月' + str(day) + '日'


# ----------------------------------------------------- Test Code ------------------------------------------------------

def __verify_year_month(time_str, year_expect, month_expect):
    times = HistoryTime.time_text_to_history_times(time_str)
    year, month, day = HistoryTime.date_of_tick(times[0])
    assert year == year_expect and month == month_expect


def test_history_time_year():
    __verify_year_month('9百年', 900, 1)
    __verify_year_month('2010年', 2010, 1)
    __verify_year_month('二千年', 2000, 1)
    __verify_year_month('公元3百年', 300, 1)
    __verify_year_month('公元三百年', 300, 1)
    __verify_year_month('一万亿年', 1000000000000, 1)

    __verify_year_month('公元前1900年', -1900, 1)
    __verify_year_month('公元前500年', -500, 1)
    __verify_year_month('前一百万年', -1000000, 1)
    __verify_year_month('前200万年', -2000000, 1)
    __verify_year_month('前一万亿年', -1000000000000, 1)


def test_history_time_year_month():
    __verify_year_month('1900年元月', 1900, 1)
    __verify_year_month('1900年正月', 1900, 1)

    __verify_year_month('1900年一月', 1900, 1)
    __verify_year_month('1900年二月', 1900, 2)
    __verify_year_month('1900年三月', 1900, 3)
    __verify_year_month('1900年四月', 1900, 4)
    __verify_year_month('1900年五月', 1900, 5)
    __verify_year_month('1900年六月', 1900, 6)
    __verify_year_month('1900年七月', 1900, 7)
    __verify_year_month('1900年八月', 1900, 8)
    __verify_year_month('1900年九月', 1900, 9)
    __verify_year_month('1900年十月', 1900, 10)
    __verify_year_month('1900年十一月', 1900, 11)
    __verify_year_month('1900年十二月', 1900, 12)

    # --------------------------------------------------

    __verify_year_month('公元前200年', -200, 1)

    __verify_year_month('公元前200年元月', -200, 1)
    __verify_year_month('公元前200年正月', -200, 1)

    __verify_year_month('公元前200年一月', -200, 1)
    __verify_year_month('公元前200年二月', -200, 2)
    __verify_year_month('公元前200年三月', -200, 3)
    __verify_year_month('公元前200年四月', -200, 4)
    __verify_year_month('公元前200年五月', -200, 5)
    __verify_year_month('公元前200年六月', -200, 6)
    __verify_year_month('公元前200年七月', -200, 7)
    __verify_year_month('公元前200年八月', -200, 8)
    __verify_year_month('公元前200年九月', -200, 9)
    __verify_year_month('公元前200年十月', -200, 10)
    __verify_year_month('公元前200年十一月', -200, 11)
    __verify_year_month('公元前200年十二月', -200, 12)


def test_time_text_to_history_times():
    # times = HistoryTime.time_text_to_history_times('220 - 535')
    # assert HistoryTime.year_of_tick(times[0]) == 220 and HistoryTime.year_of_tick(times[1]) == 535

    times = HistoryTime.time_text_to_history_times('公元前1600年 - 公元前1046年')
    assert HistoryTime.year_of_tick(times[0]) == -1600 and HistoryTime.year_of_tick(times[1]) == -1046


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    test_history_time_year()
    test_history_time_year_month()
    test_time_text_to_history_times()
    print('All test passed.')


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





