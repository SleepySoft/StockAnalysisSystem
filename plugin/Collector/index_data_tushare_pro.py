import pandas as pd
import tushare as ts

from StockAnalysisSystem.core.config import TS_TOKEN
from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.CollectorUtility import *


# ------------------------------------------------------- Fields -------------------------------------------------------

FIELDS = {
    'TradeData.Index.Daily': {
        'ts_code':                       'TS指数代码',
        'trade_date':                    '交易日',
        'close':                         '收盘点位',
        'open':                          '开盘点位',
        'high':                          '最高点位',
        'low':                           '最低点位',
        'pre_close':                     '昨日收盘点',
        'change':                        '涨跌点',
        'pct_chg':                       '涨跌幅',                            # （%）
        'vol':                           '成交量',                            # （手）
        'amount':                        '成交额',                            # （千元）
    },
}


# -------------------------------------------------------- Prob --------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_name': 'index_data_tushare_pro',
        'plugin_version': '0.0.0.1',
        'tags': ['tusharepro']
    }


def plugin_adapt(uri: str) -> bool:
    return uri in FIELDS.keys()


def plugin_capacities() -> list:
    return list(FIELDS.keys())


# ----------------------------------------------------------------------------------------------------------------------

def __fetch_index_data_daily(**kwargs) -> pd.DataFrame:
    uri = kwargs.get('uri')
    result = check_execute_test_flag(**kwargs)

    if result is None:
        period = kwargs.get('trade_date')

        ts_code = pickup_ts_code(kwargs)
        since, until = normalize_time_serial(period, default_since(), today())

        pro = ts.pro_api(TS_TOKEN)
        time_iter = DateTimeIterator(since, until)

        result = None
        while not time_iter.end():
            # 8000 items per one time
            sub_since, sub_until = time_iter.iter_years(25)
            ts_since = sub_since.strftime('%Y%m%d')
            ts_until = sub_until.strftime('%Y%m%d')

            clock = Clock()
            sub_result = pro.index_daily(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
            print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

            result = pd.concat([result, sub_result], ignore_index=True)

    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        result['trade_date'] = pd.to_datetime(result['trade_date'])
        result['stock_identity'] = result['ts_code'].apply(ts_code_to_stock_identity)
    return result


# ----------------------------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri in list(FIELDS.keys()):
        return __fetch_index_data_daily(**kwargs)
    else:
        return None


def validate(**kwargs) -> bool:
    nop(kwargs)
    return True


def fields() -> dict:
    return FIELDS



