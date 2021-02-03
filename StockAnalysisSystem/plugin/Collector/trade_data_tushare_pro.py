import pandas as pd
import tushare as ts

from StockAnalysisSystem.core.config import TS_TOKEN
from StockAnalysisSystem.core.Utility.common import *
from StockAnalysisSystem.core.Utility.df_utility import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.Utility.CollectorUtility import *


# ------------------------------------------------------- Fields -------------------------------------------------------

FIELDS = {
    'TradeData.Stock.Daily': {
        'ts_code':                       '股票代码',
        'trade_date':                    '交易日期',

        # daily()
        'open':                          '开盘价',
        'high':                          '最高价',
        'low':                           '最低价',
        'close':                         '收盘价',
        'pre_close':                     '昨收价',
        'change':                        '涨跌额',
        'pct_chg':                       '涨跌幅',                            # （未复权，如果是复权请用 通用行情接口 ）
        'vol':                           '成交量',                            # （手）
        'amount':                        '成交额',                            # （千元）

        # adj_factor()
        'adj_factor':                    '复权因子',
    },
}


# -------------------------------------------------------- Prob --------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_name': 'trade_data_tushare_pro',
        'plugin_version': '0.0.0.1',
        'tags': ['tusharepro']
    }


def plugin_adapt(uri: str) -> bool:
    return uri in FIELDS.keys()


def plugin_capacities() -> list:
    return list(FIELDS.keys())


# ----------------------------------------------------------------------------------------------------------------------

ts_daily_delay = Delayer(int(60 * 1000 / 500))


def __fetch_trade_data_daily(**kwargs) -> pd.DataFrame:
    uri = kwargs.get('uri')
    result = check_execute_test_flag(**kwargs)

    if result is None:
        period = kwargs.get('trade_date')

        ts_code = pickup_ts_code(kwargs)
        since, until = normalize_time_serial(period, default_since(), today())

        pro = ts.pro_api(TS_TOKEN)
        time_iter = DateTimeIterator(since, until)

        result = None
        while True:
            sub_since, sub_until = time_iter.iter_years(20)
            ts_since = sub_since.strftime('%Y%m%d')
            ts_until = sub_until.strftime('%Y%m%d')

            # 500 times per 1 min, do not need delay.
            clock = Clock()

            # Score: Na; Update 15:00 ~ 16:00; 500 queries per one min, 5000 data per one time;
            # Score: 5000 - No limit.
            ts_daily_delay.delay()
            result_daily = pro.daily(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
            # Score: Na; Update: 09:30; No limit
            # Note that the adjust factor can not be fetched by slice
            result_adjust = pro.adj_factor(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
            # Score 300; Update 15:00 ~ 17:00; No limit;
            # result_index = pro.daily_basic(ts_code=ts_code, start_date=ts_since, end_date=ts_until)

            print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

            sub_result = None
            sub_result = merge_on_columns(sub_result, result_daily, ['ts_code', 'trade_date'])
            sub_result = merge_on_columns(sub_result, result_adjust, ['ts_code', 'trade_date'])
            # sub_result = merge_on_columns(sub_result, result_index, ['ts_code', 'trade_date'])

            result = pd.concat([result, sub_result], ignore_index=True)

            if time_iter.end():
                break

    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        result['stock_identity'] = result['ts_code']
        result['stock_identity'] = result['stock_identity'].str.replace('.SH', '.SSE')
        result['stock_identity'] = result['stock_identity'].str.replace('.SZ', '.SZSE')
        result['trade_date'] = pd.to_datetime(result['trade_date'])
    return result


# ----------------------------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri in list(FIELDS.keys()):
        return __fetch_trade_data_daily(**kwargs)
    else:
        return None


def validate(**kwargs) -> bool:
    nop(kwargs)
    return True


def fields() -> dict:
    return FIELDS



