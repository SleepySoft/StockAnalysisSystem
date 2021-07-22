import pandas as pd
from os import path

from .common import *
from .time_utility import *


# Tushare access limit, as fetch times per minute.
# If fetch data from tushare gets error message like: "抱歉，您每分钟最多访问该接口x次"
# Fill the x to the corresponding entry of this table
# This config is for 5000 scores. The number in comments is for 2000 or less.
#
# You can put your delay config in config.json as:
#
#    "TS_DELAY": {
#        "daily_basic":          "0",
#        "fina_mainbz":          "0",
#        ......
#    }
#

DEFAULT_TS_DELAYER_TABLE = {
    'daily_basic':          DelayerMinuteLimit(500),          # 500
    'fina_mainbz':          DelayerMinuteLimit(60),          # 60

    'fina_audit':           DelayerMinuteLimit(50),          # 50
    'balancesheet':         DelayerMinuteLimit(50),          # 50
    'income':               DelayerMinuteLimit(50),          # 50
    'cashflow':             DelayerMinuteLimit(50),          # 50

    'index_daily':          DelayerMinuteLimit(500),          # 500
    'daily_index':          DelayerMinuteLimit(500),          # 500

    'concept_detail':       DelayerMinuteLimit(100),          # 100
    'namechange':           DelayerMinuteLimit(100),          # 100

    'pledge_stat':          DelayerMinuteLimit(1200),          # 1200
    'pledge_detail':        DelayerMinuteLimit(1200),          # 1200


    'stk_holdernumber':     DelayerMinuteLimit(10),          # 10
    'top10_holders':        DelayerMinuteLimit(10),          # 10
    'top10_floatholders':   DelayerMinuteLimit(10),          # 10
    'stk_holdertrade':      DelayerMinuteLimit(300),        # 300

    'daily':                DelayerMinuteLimit(1200),          # 1200
    'adj_factor':           DelayerMinuteLimit(1200),          # 1200

    'repurchase':           DelayerMinuteLimit(20),          # 20
    'share_float':          DelayerMinuteLimit(20),          # 20
}


delayer_table = DEFAULT_TS_DELAYER_TABLE


def set_delay_table(table: dict):
    global delayer_table
    try:
        for k, v in table.items():
            delayer_table[k] = DelayerMinuteLimit(int(v))
    except Exception as e:
        delayer_table = DEFAULT_TS_DELAYER_TABLE
        print('Set delay table fail: ' + str(e))
        print('Use default delay table.')
    finally:
        pass


def ts_delay(ts_interface: str):
    delayer = delayer_table.get(ts_interface)
    if delayer is not None:
        delayer.delay()


root_path = path.dirname(path.dirname(path.abspath(__file__)))


def param_as_date_str(kwargs: dict, param: str) -> str:
    dt = kwargs.get(param)
    if dt is None:
        return ''
    if not isinstance(dt, (datetime.datetime, datetime.date, str)):
        return ''
    if isinstance(dt, str):
        dt = text2date(dt)
    return dt.strftime('%Y%m%d')


def pickup_since_until_as_date(kwargs: dict) -> (str, str):
    since = kwargs.get('since', None)
    until = kwargs.get('until', None)
    return param_as_date_str(kwargs, since), param_as_date_str(kwargs, until)


# def ts_exchange_to_stock_exchange(exchange: str) -> str:
#     return {
#         'SH': 'SSE',
#         'SZ': 'SZSE',
#     }.get(exchange, exchange)
#
#
# def ts_code_to_stock_identity(ts_code: str) -> str:
#     parts = ts_code.split('.')
#     if len(parts) != 2:
#         # Error
#         return ts_code
#     return parts[0] + '.' + ts_exchange_to_stock_exchange(parts[1])


TS_SAS_IDENTITY_SUFFIX_TABLE = [
    ('SH',    'SSE'),
    ('SZ',    'SZSE'),
    ('CSI',   'CSI'),
    ('CIC',   'CICC'),
    ('SI',    'SW'),
    ('MI',    'MSCI'),
    # 'OTH' not a valid exchange
]


BAO_SAS_IDENTITY_SUFFIX_TABLE = [
    ('sh',    'SSE'),
    ('sz',    'SZSE'),
]


def stock_identity_to_ts_code(stock_identity: str) -> str:
    for ts_suffix, sas_suffix in TS_SAS_IDENTITY_SUFFIX_TABLE:
        if stock_identity.endswith(sas_suffix):
            return stock_identity.replace(sas_suffix, ts_suffix)
    return stock_identity


def ts_code_to_stock_identity(ts_code: str) -> str:
    for ts_suffix, sas_suffix in TS_SAS_IDENTITY_SUFFIX_TABLE:
        if ts_code.endswith(ts_suffix):
            return ts_code.replace(ts_suffix, sas_suffix)
    return ts_code


def bao_code_to_stock_identity(bao_code: str) -> str:
    for bao_prefix, sas_suffix in BAO_SAS_IDENTITY_SUFFIX_TABLE:
        if bao_code.startswith(bao_prefix):
            return bao_code.replace(bao_prefix + '.', '') + '.' + sas_suffix
    return bao_code


def code_exchange_to_ts_code(code: str, exchange: str) -> str:
    for ts_suffix, sas_suffix in TS_SAS_IDENTITY_SUFFIX_TABLE:
        if exchange == sas_suffix:
            return code + '.' + ts_suffix
    return code + '.' + exchange


def code_exchange_to_bao_code(code: str, exchange: str) -> str:
    for bao_prefix, sas_suffix in BAO_SAS_IDENTITY_SUFFIX_TABLE:
        if exchange == sas_suffix:
            return bao_prefix + '.' + code
    return exchange + '.' + code


def pickup_ts_code(kwargs: dict) -> str:
    stock_identity = kwargs.get('stock_identity')
    if stock_identity is not None:
        return stock_identity_to_ts_code(stock_identity)
    code = kwargs.get('code')
    exchange = kwargs.get('exchange')
    if code is None or exchange is None:
        return ''
    if not isinstance(code, str) or not isinstance(exchange, str):
        return ''
    return code_exchange_to_ts_code(code, exchange)


def pickup_bao_code(kwargs: dict) -> str:
    stock_identity = kwargs.get('stock_identity')
    if stock_identity is not None:
        return stock_identity_to_ts_code(stock_identity)
    code = kwargs.get('code')
    exchange = kwargs.get('exchange')
    if code is None or exchange is None:
        return ''
    if not isinstance(code, str) or not isinstance(exchange, str):
        return ''
    return code_exchange_to_bao_code(code, exchange)


def path_from_plugin_param(**kwargs) -> str:
    uri = kwargs.get('uri')
    file = uri.replace('.', '_')
    return root_path + '/TestData/' + file + '.csv'


def check_execute_test_flag(**kwargs) -> pd.DataFrame or None:
    if kwargs.get('test_flag', False):
        uri = path_from_plugin_param(**kwargs)
        return pd.DataFrame.from_csv(uri)
    return None


def check_execute_dump_flag(result: pd.DataFrame, **kwargs):
    if kwargs.get('dump_flag', False):
        uri = path_from_plugin_param(**kwargs)
        result.to_csv(uri)


def is_slice_update(ts_code: str, since: datetime.datetime, until: datetime.datetime) -> bool:
    return not str_available(ts_code) and isinstance(since, datetime.datetime)




