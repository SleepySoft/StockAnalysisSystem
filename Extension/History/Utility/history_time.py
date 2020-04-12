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
    TICK_MIN = TICK_SEC * 60            # 60
    TICK_HOUR = TICK_MIN * 60           # 3600
    TICK_DAY = TICK_HOUR * 24           # 86400
    TICK_MONTH_AVG = TICK_DAY * 30      # 2592000
    TICK_YEAR = TICK_DAY * 365          # 31536000
    TICK_LEAP_YEAR = TICK_DAY * 366     # 31622400
    TICK_WEEK = TICK(TICK_YEAR / 52)    # 608123.0769230769
    TICK_MONTH = [1,
                  31 * TICK_DAY, 60 * TICK_DAY, 91 * TICK_DAY, 121 * TICK_DAY,
                  152 * TICK_DAY, 182 * TICK_DAY, 213 * TICK_DAY, 244 * TICK_DAY,
                  274 * TICK_DAY, 304 * TICK_DAY, 335 * TICK_DAY, 366 * TICK_DAY]

    MONTH_DAYS = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    MONTH_DAYS_LEAP_YEAR = [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    MONTH_SEC_LEAP_YEAR = [
        0 * TICK_DAY,
        31 * TICK_DAY, 60 * TICK_DAY, 91 * TICK_DAY, 121 * TICK_DAY,
        152 * TICK_DAY, 182 * TICK_DAY, 213 * TICK_DAY, 244 * TICK_DAY,
        274 * TICK_DAY, 305 * TICK_DAY, 335 * TICK_DAY, 366 * TICK_DAY,
    ]

    MONTH_SEC = [
        0 * TICK_DAY,
        31 * TICK_DAY, 59 * TICK_DAY, 90 * TICK_DAY, 120 * TICK_DAY,
        151 * TICK_DAY, 181 * TICK_DAY, 212 * TICK_DAY, 243 * TICK_DAY,
        273 * TICK_DAY, 304 * TICK_DAY, 334 * TICK_DAY, 365 * TICK_DAY,
    ]
    MONTH_SEC_LEAP_YEAR = [
        0 * TICK_DAY,
        31 * TICK_DAY, 60 * TICK_DAY, 91 * TICK_DAY, 121 * TICK_DAY,
        152 * TICK_DAY, 182 * TICK_DAY, 213 * TICK_DAY, 244 * TICK_DAY,
        274 * TICK_DAY, 305 * TICK_DAY, 335 * TICK_DAY, 366 * TICK_DAY,
    ]

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

    # @staticmethod
    # def year(year: int = 1) -> TICK:
    #     return year * HistoryTime.TICK_YEAR
    #
    # @staticmethod
    # def month(month: int = 1) -> TICK:
    #     month = max(month, 1)
    #     month = min(month, 12)
    #     return HistoryTime.TICK_MONTH[month - 1]
    #
    # @staticmethod
    # def week(week: int = 1) -> TICK:
    #     return int(week * HistoryTime.TICK_WEEK)
    #
    # @staticmethod
    # def day(day: int = 1) -> TICK:
    #     return int(day * HistoryTime.TICK_DAY)

    # ------------------------------------------------------------------------------------------------------------------
    # ---------------------------------------------------- Convert -----------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    @staticmethod
    def pytime_to_tick(ts: time.struct_time) -> TICK:
        return HistoryTime.date_time_to_ad_seconds(ts.tm_year, ts.tm_mon, ts.tm_mday,
                                                   ts.tm_hour, ts.tm_min, ts.tm_sec)

    # @staticmethod
    # def year_of_tick(tick: TICK) -> int:
    #     return HistoryTime.ad_second_to_year(tick)[0]
    #
    # @staticmethod
    # def month_of_tick(tick: TICK) -> int:
    #     return HistoryTime.ad_seconds_to_date(tick)[1]
    #
    # @staticmethod
    # def day_of_tick(tick: TICK) -> int:
    #     return HistoryTime.date_of_tick(tick)[2]
    #
    # @staticmethod
    # def date_of_tick(tick: TICK) -> (int, int, int):
    #     sign = 1 if tick >= 0 else -1
    #     day = 0
    #     year = sign * int(abs(tick) / HistoryTime.TICK_YEAR)
    #     month = 12
    #     year_mod = abs(tick) % HistoryTime.TICK_YEAR
    #     for i in range(0, len(HistoryTime.TICK_MONTH)):
    #         if year_mod <= HistoryTime.TICK_MONTH[i]:
    #             day_tick = year_mod if i == 0 else year_mod - HistoryTime.TICK_MONTH[i - 1]
    #             day = day_tick / HistoryTime.day()
    #             month = i + 1
    #             break
    #     return int(year), int(month), int(day)
    #
    # @staticmethod
    # def decimal_year_to_tick(year: float) -> TICK:
    #     return int(year * HistoryTime.TICK_YEAR)
    #
    # @staticmethod
    # def tick_to_decimal_year(tick: TICK) -> float:
    #     return HistoryTime.round_decimal_year(float(tick) / HistoryTime.TICK_YEAR)

    @staticmethod
    def tick_to_standard_string(tick: TICK, show_date: bool = False, show_time: bool = False) -> str:
        year, month, day, _ = HistoryTime.ad_seconds_to_date(tick)
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

    # @staticmethod
    # def round_decimal_year(year: float):
    #     return round(year, HistoryTime.EFFECTIVE_TIME_DIGIT)
    #
    # @staticmethod
    # def decimal_year_equal(digital1: float, digital2: float):
    #     return abs(digital1 - digital2) < pow(1.0, -(HistoryTime.EFFECTIVE_TIME_DIGIT + 1))
    #
    # @staticmethod
    # def build_history_time_tick(year: int = 0, month: int = 0, day: int = 0,
    #                             hour: int = 0, minute: int = 0, second: int = 0,
    #                             week: int = 0) -> TICK:
    #     sign = 1 if year >= 0 else -1
    #     tick = HistoryTime.year(abs(year)) + HistoryTime.month(month) + HistoryTime.day(day) + \
    #         hour * HistoryTime.TICK_HOUR + minute * HistoryTime.TICK_MIN + second * HistoryTime.TICK_MIN + \
    #         week * HistoryTime.TICK_WEEK
    #     return sign * tick

    # ------------------------------------------------------------------------------------------------------------------
    # -------------------------------------------- Text Analysis and Parse ---------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

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
            return HistoryTime.date_time_to_ad_seconds(sign * int(number_str), 1, 1)
        else:
            year = sign * str_to_int(year)
            month = str_to_int(month)
            day = str_to_int(day)

            year = 1 if year == 0 else year
            month = max(month, 1)
            month = min(month, 12)
            day = max(day, 1)
            day = min(day, HistoryTime.month_days(abs(year))[month])

            return HistoryTime.date_time_to_ad_seconds(year, month, day)

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
        year, month, day, _ = HistoryTime.ad_seconds_to_date(his_tick)
        if year < 0:
            text = '公元前' + str(-year) + '年'
        else:
            text = '公元' + str(-year) + '年'
        return text + str(month) + '月' + str(day) + '日'

    # ------------------------------------------------------------------------------------------------------------------
    # -------------------------------------------- Strict DateTime From AD ---------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    # --------------------------------------- Constant ---------------------------------------

    @staticmethod
    def year_ticks(year: int) -> int:
        assert year > 0
        return HistoryTime.TICK_LEAP_YEAR if HistoryTime.is_leap_year(year) else HistoryTime.TICK_YEAR

    @staticmethod
    def month_ticks(year: int) -> [int]:
        assert year > 0
        return HistoryTime.MONTH_SEC_LEAP_YEAR if HistoryTime.is_leap_year(year) else HistoryTime.MONTH_SEC

    @staticmethod
    def month_days(year: int) -> [int]:
        if year <= 0:
            assert False
        return HistoryTime.MONTH_DAYS_LEAP_YEAR if HistoryTime.is_leap_year(year) else HistoryTime.MONTH_DAYS

    # -------------------------------------- Time Delta --------------------------------------

    @staticmethod
    def offset_ad_second(tick: TICK, offset_year: int, offset_month: int, offset_day: int,
                         offset_hour: int, offset_minute: int, offset_second: int) -> TICK:
        tick += offset_day * HistoryTime.TICK_DAY + \
                offset_hour * HistoryTime.TICK_HOUR + \
                offset_minute * HistoryTime.TICK_MIN + \
                offset_second * HistoryTime.TICK_SEC
        year, month, day, remainder = HistoryTime.ad_seconds_to_date(tick)

        month += offset_month
        if month > 0:
            offset_year += (month - 1) // 12
            month = (month - 1) % 12 + 1
        else:
            # If month = -11, then the offset year is -1 and the complement month is  1 (-1 * 12 + 1 = -11)
            # If month = -12, then the offset year is -2 and the complement month is 12 (-2 * 12 + 12 = -12)
            # If month = -13, then the offset year is -2 and the complement month is 11 (-2 * 12 + 11 = -13)
            month_year = abs(month) // 12 + 1
            complement_month = month_year * 12 + month
            offset_year -= month_year
            month = complement_month

        # If year is 1, and offset_year is -1, the result should be -1, because there's no 0 year.
        # So if year is 10, and offset_year is -10, the -1 branch will be reached
        # Else if year is less than 0 or offset_year is larger than 0, the -1 branch will not be reached
        if 0 < year <= -offset_year:
            year += offset_year - 1
        elif -offset_year <= year < 0:
            year += offset_year + 1
        else:
            year += offset_year

        month_days = HistoryTime.month_days(abs(year))
        day = min(day, month_days[month])

        return HistoryTime.date_time_to_ad_seconds(year, month, day, 0, 0, 0) + remainder

    @staticmethod
    def offset_date_time(origin: (int, int, int, int, int, int),
                         offset: (int, int, int, int, int, int)) -> (int, int, int, int, int, int):
        tick = HistoryTime.date_time_to_ad_seconds(*origin)
        offset_tick = HistoryTime.offset_ad_second(tick, *offset)
        return HistoryTime.ad_seconds_to_date_time(offset_tick)

    # ---------------------------------- Basic Calculation -----------------------------------

    @staticmethod
    def is_leap_year(year: int) -> bool:
        """
        Check whether the year is leap year.
        :param year: Since 0001
        :return: True if it's leap year else False
        """
        year = abs(int(year))
        assert year != 0
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    @staticmethod
    def leap_year_count_since_ad(year: int) -> int:
        """
        Concept: Leap year should exclude the 25th, 50th, 75th, keep 100th, exclude 125th, 150th, ...
        :param year: Since 0001
        :return: Leap year count that include this year itself
        """
        year = 1 if year == 0 else abs(year)
        rough_count = year // 4
        except_count = rough_count - rough_count // 25 + rough_count // 100
        return except_count

    @staticmethod
    def year_to_second(year: int) -> int:
        """
        Calculate the seconds since 0001 to the end of specified year.
        :param year: Since 0001
        :return: The seconds
        """
        assert year >= 0
        if year == 0:
            return 0
        leap_years = HistoryTime.leap_year_count_since_ad(year)
        year_seconds = year * HistoryTime.TICK_YEAR + leap_years * HistoryTime.TICK_DAY
        return year_seconds

    @staticmethod
    def ad_second_to_year(sec: int) -> (int, int):
        """
        Convert AD since seconds to years. Notice the year starts from 0
        :param sec: The second since AD which should be larger than 0
        :return: Year - Start from 0 if the seconds is less than a year
                  Remainder - Remainder of Seconds less than a year
        """
        assert sec >= 0
        rough_years = sec // HistoryTime.TICK_YEAR

        while True:
            leap_year_count = HistoryTime.leap_year_count_since_ad(rough_years)
            precise_year_days = rough_years * 365 + leap_year_count
            remaining_sec = sec - precise_year_days * HistoryTime.TICK_DAY
            if remaining_sec < 0:
                rough_years -= 1
            else:
                break
        assert remaining_sec < HistoryTime.year_ticks(rough_years + 1)
        return rough_years, remaining_sec

    # ---------------------------------- Offset Calculation ----------------------------------

    # @staticmethod
    # def offset_bc_tick_to_ad(sec: int) -> (int, int):
    #     """
    #     It's hard to calculate the Date of BC directly.
    #     We can offset the AD origin for years.
    #     Then minus the offset years from the result.
    #     :param sec: The ticks we want to offset.
    #     :return: Tick - The tick after offset
    #               Year - The years that we offset
    #     """
    #     if sec >= 0:
    #         return sec, 0
    #     abs_year, remaining_sec = HistoryTime.ad_second_to_year(-sec)
    #     offset_year = abs_year if remaining_sec == 0 else abs_year + 1
    #     offset_year_ticks = HistoryTime.year_to_second(offset_year)
    #     return sec + offset_year_ticks, offset_year + 1

    @staticmethod
    def offset_bc_year_to_ad(year: int) -> (int, int):
        """
        It's hard to calculate the Date of BC directly.
        We can offset the AD origin for years.
        Then minus the offset years from the result.
        :param year: The year we want to offset.
        :return: Tick - The tick after offset
                  Year - The years that we offset
        """
        if year >= 0:
            return 0, year
        offset_year = -year
        offset_year_ticks = HistoryTime.year_to_second(offset_year)
        # Note that there's no 0 year. So from -1 year to 1 year, it only shifts 1 year
        # And if we offset it's absolute years, the original year is always 1
        return offset_year_ticks, 1

    # ---------------------------------- Second to Date Time ----------------------------------

    @staticmethod
    def seconds_to_month(sec: int, year: int = 0) -> (int, int):
        """
        Convert seconds to month considering the size of the month and leap years
        :param sec: The seconds
        :param year: Year start from 0001, for checking leap year. If it's 0, it will try to get year from sec
        :return: Month - Start from 1
                 Remainder of Seconds
        """
        if year == 0:
            year, sec = HistoryTime.ad_second_to_year(sec)
        leap_year = HistoryTime.is_leap_year(year)
        year_sec = HistoryTime.TICK_LEAP_YEAR if leap_year else HistoryTime.TICK_YEAR
        if sec > year_sec:
            sec = sec % year_sec
        month_sec = HistoryTime.MONTH_SEC_LEAP_YEAR if leap_year else HistoryTime.MONTH_SEC

        month = 1
        while month < len(month_sec):
            if month_sec[month] > sec:
                break
            month += 1
        return month, sec - month_sec[month - 1]

    @staticmethod
    def seconds_to_day(sec: int) -> (int, int):
        """
        Convert seconds to days
        :param sec: Seconds
        :return: Days - Start from 0
                 Remainder of Seconds
        """
        return sec // HistoryTime.TICK_DAY, sec % HistoryTime.TICK_DAY

    @staticmethod
    def seconds_to_time(sec: int) -> (int, int, int):
        """
        Convert seconds to hour, minutes and seconds
        :param sec: Seconds
        :return: Hour - 0 ~ max
                 Minutes - 0 ~ 59
                 Seconds - 0 ~ 59
        """
        hour = sec // HistoryTime.TICK_HOUR
        sec_min = sec % HistoryTime.TICK_HOUR
        minute = sec_min // HistoryTime.TICK_MIN
        seconds = sec_min % HistoryTime.TICK_MIN
        return hour, minute, seconds

    @staticmethod
    def ad_seconds_to_date(sec: int) -> (int, int, int, int):
        """
        Convert AD since seconds to date
        :param sec: Seconds since AD
        :return: Year - 1 ~  max
                 Month - 1 ~12
                 Day - 1 ~ 31
                 Remainder of Seconds - 0 ~ 86400
        """
        if sec >= 0:
            year, remainder = HistoryTime.ad_second_to_year(sec)
            month, remainder = HistoryTime.seconds_to_month(remainder, year + 1)
            day, remainder = HistoryTime.seconds_to_day(remainder)
            return year + 1, month, day + 1, remainder
        else:
            abs_year, remaining_sec = HistoryTime.ad_second_to_year(-sec)
            offset_year = abs_year if remaining_sec == 0 else abs_year + 1
            offset_year_ticks = HistoryTime.year_to_second(offset_year)
            offset_tick = sec + offset_year_ticks

            month, remainder = HistoryTime.seconds_to_month(offset_tick, offset_year)
            day, remainder = HistoryTime.seconds_to_day(remainder)

            return -offset_year, month, day + 1, remainder

    @staticmethod
    def ad_seconds_to_date_time(sec: int) -> (int, int, int, int, int, int):
        """
        Convert AD since seconds to date time
        :param sec: Seconds since AD
        :return: Year - 1 ~  max
                 Month - 1 ~12
                 Day - 1 ~ 31
                 Hour - 0 ~ 23
                 Minutes - 0 ~ 59
                 Seconds - 0 ~ 59
        """
        year, month, day, remainder = HistoryTime.ad_seconds_to_date(sec)
        hour, minute, seconds = HistoryTime.seconds_to_time(remainder)
        return year, month, day, hour, minute, seconds

    # ---------------------------------- Date Time to Second ----------------------------------

    @staticmethod
    def time_to_seconds(hours: int = 0, minutes: int = 0, seconds: int = 0) -> TICK:
        return hours * HistoryTime.TICK_HOUR + minutes * HistoryTime.TICK_MIN + seconds

    @staticmethod
    def date_time_to_ad_seconds(year: int, month: int, day: int,
                                hours: int = 0, minutes: int = 0, seconds: int = 0) -> TICK:
        assert 1 <= month <= 12

        month_sec = HistoryTime.month_ticks(abs(year))
        offset_year_ticks, offset_year = HistoryTime.offset_bc_year_to_ad(year)

        offset_year = HistoryTime.__shrink_edge(offset_year)
        month = HistoryTime.__shrink_edge(month)
        day = HistoryTime.__shrink_edge(day)

        year_seconds = HistoryTime.year_to_second(offset_year)
        month_seconds = month_sec[month]
        day_seconds = day * HistoryTime.TICK_DAY

        ad_tick = year_seconds + month_seconds + day_seconds + HistoryTime.time_to_seconds(hours, minutes, seconds)
        return ad_tick - offset_year_ticks

    @staticmethod
    def __shrink_edge(num: int) -> int:
        if num > 0:
            return num - 1
        if num < 0:
            return num + 1
        else:
            return num


# ----------------------------------------------------- Test Code ------------------------------------------------------

f = open('history_time.log', 'wt')


def __log_error(text: str):
    f.write(text)
    f.flush()


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


def test_ad_since_tick():
    year, month, day, hour, minutes, sec = HistoryTime.ad_seconds_to_date_time(0)
    assert (year, month, day, hour, minutes, sec) == (1, 1, 1, 0, 0, 0)

    year, month, day, hour, minutes, sec = HistoryTime.ad_seconds_to_date_time(HistoryTime.TICK_DAY - 1)
    assert (year, month, day, hour, minutes, sec) == (1, 1, 1, 23, 59, 59)

    year, month, day, hour, minutes, sec = HistoryTime.ad_seconds_to_date_time(HistoryTime.TICK_DAY)
    assert (year, month, day, hour, minutes, sec) == (1, 1, 2, 0, 0, 0)

    year, month, day, hour, minutes, sec = HistoryTime.ad_seconds_to_date_time(HistoryTime.TICK_YEAR - 1)
    assert (year, month, day, hour, minutes, sec) == (1, 12, 31, 23, 59, 59)

    year, month, day, hour, minutes, sec = HistoryTime.ad_seconds_to_date_time(HistoryTime.TICK_YEAR)
    assert (year, month, day, hour, minutes, sec) == (2, 1, 1, 0, 0, 0)

    year, month, day, hour, minutes, sec = HistoryTime.ad_seconds_to_date_time(HistoryTime.TICK_YEAR * 4)
    assert (year, month, day, hour, minutes, sec) == (4, 12, 31, 0, 0, 0)

    year, month, day, hour, minutes, sec = HistoryTime.ad_seconds_to_date_time(HistoryTime.TICK_YEAR * 3 + HistoryTime.TICK_LEAP_YEAR)
    assert (year, month, day, hour, minutes, sec) == (5, 1, 1, 0, 0, 0)


def test_datetime_to_tick():
    ad_tick = HistoryTime.date_time_to_ad_seconds(1, 1, 1, 0, 0, 0)
    assert ad_tick == 0

    ad_tick = HistoryTime.date_time_to_ad_seconds(1, 1, 1, 23, 59, 59)
    assert ad_tick == HistoryTime.TICK_DAY - 1

    ad_tick = HistoryTime.date_time_to_ad_seconds(1, 1, 2, 0, 0, 0)
    assert ad_tick == HistoryTime.TICK_DAY

    ad_tick = HistoryTime.date_time_to_ad_seconds(1, 12, 31, 23, 59, 59)
    assert ad_tick == HistoryTime.TICK_YEAR - 1

    ad_tick = HistoryTime.date_time_to_ad_seconds(2, 1, 1, 0, 0, 0)
    assert ad_tick == HistoryTime.TICK_YEAR

    ad_tick = HistoryTime.date_time_to_ad_seconds(4, 12, 31, 0, 0, 0)
    assert ad_tick == HistoryTime.TICK_YEAR * 4

    ad_tick = HistoryTime.date_time_to_ad_seconds(5, 1, 1, 0, 0, 0)
    assert ad_tick == HistoryTime.TICK_YEAR * 3 + HistoryTime.TICK_LEAP_YEAR


def __verify_time_offset(origin: (int, int, int, int, int, int),
                         offset: (int, int, int, int, int, int),
                         expect: (int, int, int, int, int, int)):
    result = HistoryTime.offset_date_time(origin, offset)
    if result != expect:
        print('%s + %s -> %s != %s' % (str(origin), str(offset), str(result), str(expect)))
        assert False


def test_time_offset():
    __verify_time_offset((1, 12, 31, 0, 0, 0), (0, -12, 0, 0, 0, 0), (-1, 12, 31, 0, 0, 0))
    __verify_time_offset((1, 12, 31, 0, 0, 0), (-1,  0, 0, 0, 0, 0), (-1, 12, 31, 0, 0, 0))
    __verify_time_offset((1, 12, 31, 23, 59, 59), (0, -13, 0, 0, 0, 0), (-1, 11, 30, 23, 59, 59))

    __verify_time_offset((1, 3, 31, 0, 0, 0), (0, -1, 0, 0, 0, 0), (1, 2, 28, 0, 0, 0))
    __verify_time_offset((4, 3, 31, 23, 59, 59), (0, -1, 0, 0, 0, 0), (4, 2, 29, 23, 59, 59))


def __cross_verify_tick_datetime(*args):
    ad_tick = HistoryTime.date_time_to_ad_seconds(*args)
    date_time = HistoryTime.ad_seconds_to_date_time(ad_tick)
    if date_time != args:
        print('Error: ' + str(args) + ' -> ' + str(date_time))
        __log_error('Error: ' + str(args))


def test_batch_ad_conversion():
    for year in range(0, 3000):
        for month in range(0, 12):
            month_days = HistoryTime.month_days(year + 1)
            for day in range(0, month_days[month + 1]):
                for hour in [0, 8, 16, 23]:
                    for minute in [0, 30, 59]:
                        for second in [0, 30, 59]:
                            __cross_verify_tick_datetime(year + 1, month + 1, day + 1, hour, minute, second)
            print('AD %04d-%02d is OK.' % (year + 1, month + 1))


def test_batch_bc_conversion():
    for year in range(0, -3000, -1):
        for month in range(0, 12):
            month_days = HistoryTime.month_days(abs(year - 1))
            for day in range(0, month_days[month + 1]):
                for hour in [0, 8, 16, 23]:
                    for minute in [0, 30, 59]:
                        for second in [0, 30, 59]:
                            __cross_verify_tick_datetime(year - 1, month + 1, day + 1, hour, minute, second)
            print('BC %04d-%02d is OK.' % (-(year - 1), month + 1))


def __manual_check_continuity_of_datetime_to_tick_single(sec: int):
    date_time = HistoryTime.ad_seconds_to_date_time(sec)
    seconds = HistoryTime.date_time_to_ad_seconds(*date_time)

    success = (seconds == sec)
    text = str(sec) + ' -> ' + str(date_time) + ' -> ' + str(seconds) + ' : ' + ('PASS' if success else 'FAIL')

    print(text)
    if not success:
        __log_error(text)
        print('-------------------------------------------------')


def manual_check_continuity_of_datetime_to_tick():
    for i in range(0, -9999999999, -3600):
        __manual_check_continuity_of_datetime_to_tick_single(i)


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    __cross_verify_tick_datetime(-3, 1, 1, 0, 0, 0)
    __cross_verify_tick_datetime(-4, 1, 1, 0, 0, 30)
    __cross_verify_tick_datetime(-4, 2, 29, 0, 0, 0)
    __cross_verify_tick_datetime(-4, 12, 31, 0, 0, 0)

    test_history_time_year()
    test_history_time_year_month()
    test_time_text_to_history_times()
    test_ad_since_tick()
    test_datetime_to_tick()

    test_time_offset()

    test_batch_ad_conversion()
    test_batch_bc_conversion()
    manual_check_continuity_of_datetime_to_tick()

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





