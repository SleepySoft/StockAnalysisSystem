import pandas as pd
import tushare as ts

from StockAnalysisSystem.core.config import TS_TOKEN
from StockAnalysisSystem.core.Utility.common import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.Utility.CollectorUtility import *


FIELDS = {
    'Stockholder.Repurchase': {

    },
    'Stockholder.StockUnlock': {

    },
}


def plugin_prob() -> dict:
    return {
        'plugin_name': 'dummy_plugin_for_test',
        'plugin_version': '0.0.0.1',
        'tags': ['repurchase', 'unlimit', 'tushare', 'ZhangShen', 'Sleepy']
    }


def plugin_adapt(uri: str) -> bool:
    return uri in FIELDS.keys()


def plugin_capacities() -> list:
    return list(FIELDS.keys())


# ---------------------------------------------------------------------------------------------------

def update_repurchase_and_stock_unlock(**kwargs) -> pd.DataFrame or None:
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
        if uri == 'Stockholder.Repurchase':
            # In fact, no company can repurchase up to 2000 times
            sub_result: pd.DataFrame = pro.repurchase(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
        elif uri == 'Stockholder.StockUnlock':
            sub_result: pd.DataFrame = pro.share_float(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
        else:
            break
        result: pd.DataFrame = pd.concat([result, sub_result])

        # 如果达不到限制（repurchase - 2000， share_float - 5000，取小的），说明已经取完数据了
        if sub_result is None or len(sub_result) < 2000:
            break

        # 此列数据可能为None
        sub_result['ann_date'].replace([None, 'None'], np.nan, inplace=True)
        sub_result['ann_date'] = sub_result['ann_date'].fillna(method='ffill')

        # 拿更新到的最近日期作为开始日期再更新一次
        last_update_day = max(sub_result['ann_date'])
        last_update_day = to_py_datetime(last_update_day)
        if last_update_day >= until:
            break
        last_update_date_str = last_update_day.strftime('%Y%m%d')

        if last_update_date_str <= ts_since:
            # tushare bug: 002939.SZ, Since 20181025, Until 20210304
            # Get data time range less than specified, which causes dead loop.
            print('Bug detected: %s (%s - %s).' % (ts_code, ts_since, ts_until))
            break
        else:
            ts_since = last_update_date_str

    print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

    if result is not None and not result.empty:
        # 将ts返回的字符串时间转化为datetime
        result['ann_date'] = pd.to_datetime(result['ann_date'])

        if uri == 'Stockholder.Repurchase':
            # 注意只有repurchase有此列
            result['end_date'] = pd.to_datetime(result['end_date'])
            result['exp_date'] = pd.to_datetime(result['exp_date'])
        elif uri == 'Stockholder.StockUnlock':
            # 将float_date列重命名为unlock_date，作为主键之一
            result['unlock_date'] = pd.to_datetime(result['float_date'])
        # 将ts_code转化为sas使用的identity
        result['stock_identity'] = result['ts_code'].apply(ts_code_to_stock_identity)

        # 如果空数据引发出错，考虑填充
        # result = result.fillna(method='ffill')

    return result


# ---------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    # 因为这两者更新过程相仿，故放在同一个函数内更新
    return update_repurchase_and_stock_unlock(**kwargs)


def validate(**kwargs) -> bool:
    pass
    return True


def fields() -> dict:
    return FIELDS

