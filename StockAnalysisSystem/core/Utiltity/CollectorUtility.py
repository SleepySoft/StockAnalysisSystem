import pandas as pd
from os import path

from .common import *
from .time_utility import *

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


def code_exchange_to_ts_code(code: str, exchange: str) -> str:
    for ts_suffix, sas_suffix in TS_SAS_IDENTITY_SUFFIX_TABLE:
        if exchange == sas_suffix:
            return code + '.' + ts_suffix
    return code + '.' + exchange


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





