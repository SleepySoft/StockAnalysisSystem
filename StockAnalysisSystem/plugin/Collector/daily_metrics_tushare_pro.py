import pandas as pd
import tushare as ts

from StockAnalysisSystem.core.config import TS_TOKEN
from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.df_utility import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.CollectorUtility import *


# ------------------------------------------------------- Fields -------------------------------------------------------

FIELDS = {
    'Metrics.Stock.Daily': {
        'ts_code':                       '股票代码',
        'trade_date':                    '交易日期',

        # daily_basic()
        'turnover_rate':                 '换手率',                            # （%）
        'turnover_rate_f':               '换手率（流通股）',                    # （自由流通股）
        'volume_ratio':                  '量比',
        'pe':                            '市盈率',                            # （总市值/净利润）
        'pe_ttm':                        '市盈率（TTM）',                      # （TTM）
        'pb':                            '市净率',                            # （总市值/净资产）
        'ps':                            '市销率',
        'ps_ttm':                        '市销率（TTM）',                      # （TTM）
        'dv_ratio':                      '股息率',                            # （%）
        'dv_ttm':                        '股息率（TTM）',                      # （%）
        'total_share':                   '总股本（万股）',                      # （万股）
        'float_share':                   '流通股本（万股）',                    # （万股）
        'free_share':                    '自由流通股本（万）',                   # （万）
        'total_mv':                      '总市值（万）',                        # （万元）
        'circ_mv':                       '流通市值（万）',                       # （万元）
    },
}


# -------------------------------------------------------- Prob --------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_name': 'daily_metrics_tushare_pro',
        'plugin_version': '0.0.0.1',
        'tags': ['tusharepro']
    }


def plugin_adapt(uri: str) -> bool:
    return uri in FIELDS.keys()


def plugin_capacities() -> list:
    return list(FIELDS.keys())


# ----------------------------------------------------------------------------------------------------------------------

ts_daily_delay = Delayer(int(60 * 1000 / 500))


def __fetch_stock_metrics_daily(**kwargs) -> pd.DataFrame:
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

            ts_daily_delay.delay()
            # Score 300; Update 15:00 ~ 17:00; No limit;
            if str_available(ts_code):
                result_metrics = pro.daily_basic(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
            else:
                result_metrics = pro.daily_basic(ts_code=ts_code, trade_date=ts_since)

            print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

            result = pd.concat([result, result_metrics], ignore_index=True)

            if time_iter.end():
                break

    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        result['stock_identity'] = result['ts_code'].apply(ts_code_to_stock_identity)
        result['trade_date'] = pd.to_datetime(result['trade_date'])
        del result['ts_code']
    return result


# ----------------------------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri in list(FIELDS.keys()):
        return __fetch_stock_metrics_daily(**kwargs)
    else:
        return None


def validate(**kwargs) -> bool:
    nop(kwargs)
    return True


def fields() -> dict:
    return FIELDS



