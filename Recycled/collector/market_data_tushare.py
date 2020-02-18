import pandas as pd
import tushare as ts
from datetime import date

try:
    import config
    from Utiltity.common import *
except Exception as e:
    from os import sys, path
    root = path.dirname(path.dirname(path.abspath(__file__)))
    sys.path.append(root)

    import config
    from Utiltity.common import *
finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------

def __fetch_trade_calender(**kwargs) -> pd.DataFrame:
    exchange = kwargs.get('exchange')
    since = kwargs.get('since')
    until = kwargs.get('until')
    if not isinstance(exchange, str) or \
       not isinstance(since, (date, str)) or \
       not isinstance(until, (date, str)):
        return None
    if isinstance(since, str):
        since = text2date(since)
    if isinstance(until, str):
        since = text2date(until)
    pro = ts.pro_api(config.TS_TOKEN)
    ts_since = since.strftime('%Y%m%d')
    ts_until = until.strftime('%Y%m%d')
    result = pro.trade_cal(exchange, start_date=ts_since, end_date=ts_until)
    if result is not None:
        result.rename(columns={'exchange': 'Exchange', 'cal_date': 'TradeDate', 'is_open': 'Status'}, inplace=True)
    return result


# ----------------------------------------------------------------------------------------------------------------------

def validate(**kwargs) -> bool:
    content = kwargs.get('content')
    return True


def fetch_data(**kwargs) -> pd.DataFrame:
    content = kwargs.get('content')
    if content == 'TradeCalender':
        return __fetch_trade_calender(**kwargs)
    else:
        return None


# ----------------------------------------------------------------------------------------------------------------------

# def plugin_prob() -> dict:
#     return {
#         'plugin_name': 'market_data_tushare',
#         'plugin_version': '0.0.0.1',
#         'tags': ['tushare']
#     }
#
#
# def plugin_capacities() -> list:
#     return [
#         'TradeCalender',
#         'SecuritiesInfo',
#         'IndexComponent',
#     ]

