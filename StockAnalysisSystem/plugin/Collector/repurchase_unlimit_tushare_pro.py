import pandas as pd
import tushare as ts

from StockAnalysisSystem.core.config import TS_TOKEN
from StockAnalysisSystem.core.Utility.common import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.Utility.CollectorUtility import *


FIELDS = {
    'Repurchase.Stock': {

    },
    'Unlimit.Stock': {

    },
}


def plugin_prob() -> dict:
    return {
        'plugin_name': 'dummy_plugin_for_test',
        'plugin_version': '0.0.0.1',
        'tags': ['repurchase', 'unlimit', 'tushare', 'ZhangShen']
    }


def plugin_adapt(uri: str) -> bool:
    return True


def plugin_capacities() -> list:  # 数据名字添加
    return list(FIELDS)


# ---------------------------------------------------------------------------------------------------

def update_repurchase(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    ann_date = kwargs.get('ann_date')

    ts_code = pickup_ts_code(kwargs)
    since, until = normalize_time_serial(ann_date, default_since(), today())

    ts_since = since.strftime('%Y%m%d')
    ts_until = until.strftime('%Y%m%d')

    pro = ts.pro_api(TS_TOKEN)

    clock = Clock()

    # ts_delay('fina_audit')

    result = None
    while True:
        sub_result = pro.repurchase(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
        result = pd.concat([result, sub_result])
        if result is None or len(sub_result) < 2000:
            break
        last_update_day = max(sub_result['ann_date'])
        last_update_day = to_py_datetime(last_update_day)
        if last_update_day >= until:
            break
        ts_since = last_update_day.strftime('%Y%m%d')

    print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

    if result is not None:
        result['stock_identity'] = result['ts_code']

        result['ann_date'] = pd.to_datetime(result['ann_date'])
        result['stock_identity'] = result['stock_identity'].str.replace('.SH', '.SSE')
        result['stock_identity'] = result['stock_identity'].str.replace('.SZ', '.SZSE')

    return result


def update_unlimit(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    ann_date = kwargs.get('ann_date')

    ts_code = pickup_ts_code(kwargs)
    since, until = normalize_time_serial(ann_date, default_since(), today())

    ts_since = since.strftime('%Y%m%d')
    ts_until = until.strftime('%Y%m%d')

    pro = ts.pro_api(TS_TOKEN)

    clock = Clock()

    # ts_delay('fina_audit')
    result = pro.share_float(ts_code=ts_code, start_date=ts_since, end_date=ts_until)

    print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

    if result is not None:
        result['stock_identity'] = result['ts_code']

        result['ann_date'] = pd.to_datetime(result['ann_date'])
        result['stock_identity'] = result['stock_identity'].str.replace('.SH', '.SSE')
        result['stock_identity'] = result['stock_identity'].str.replace('.SZ', '.SZSE')

    return result


# ---------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri == 'Repurchase.Stock':
        return update_repurchase(**kwargs)
    elif uri == 'Unlimit.Stock':
        return update_unlimit(**kwargs)
    else:
        return None


def validate(**kwargs) -> bool:
    pass
    return True


def fields() -> dict:
    return FIELDS


# def query(**kwargs) -> pd.DataFrame or None:
#     uri = kwargs.get('uri')
#     if uri == flog:
#         return pd.DataFrame({
#             'ibd': ['300783.SZ', '1StockA', '2StockB', 'StockB', 'StockC', 'StockC'],
#             'time2': [datetime(1995, 1, 1), datetime(1996, 1, 1),    # StockA
#                       datetime(2002, 2, 1), datetime(2005, 5, 1),    # StockB
#                       datetime(2020, 3, 1), datetime(2021, 1, 1)],   # StockC
#             'field11': [100., 20., 30., 40., 500., 600.],
#             'field22': ['A', 'B', 'C', 'D', 'E', 'F'],
#         })
#     else:
#         return None
















































