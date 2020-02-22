import pandas as pd
import tushare as ts
from datetime import date

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    import config
    from Utiltity.common import *
    from Utiltity.time_utility import *
    from Collector.CollectorUtility import *
except Exception as e:
    sys.path.append(root_path)

    import config
    from Utiltity.common import *
    from Utiltity.time_utility import *
    from Collector.CollectorUtility import *
finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------

FIELDS = {
    'Stockholder.PledgeStatus': {
        'ts_code':                       'TS代码',
        'end_date':                      '截至日期',
        'pledge_count':                  '质押次数',
        'unrest_pledge':                 '无限售股质押数量',
        'rest_pledge':                   '限售股份质押数量',
        'total_share':                   '总股本',
        'pledge_ratio':                  '质押比例',
    },
    'Stockholder.PledgeHistory': {
        'ts_code':                       'TS股票代码',
        'ann_date':                      '公告日期',
        'holder_name':                   '股东名称',
        'pledge_amount':                 '质押数量',
        'start_date':                    '质押开始日期',
        'end_date':                      '质押结束日期',
        'is_release':                    '是否已解押',
        'release_date':                  '解押日期',
        'pledgor':                       '质押方',
        'holding_amount':                '持股总数',
        'pledged_amount':                '质押总数',
        'p_total_ratio':                 '本次质押占总股本比例',
        'h_total_ratio':                 '持股总数占总股本比例',
        'is_buyback':                    '是否回购',
    },
}


# -------------------------------------------------------- Prob --------------------------------------------------------


def plugin_prob() -> dict:
    return {
        'plugin_name': 'stockholder_data_tushare_pro',
        'plugin_version': '0.0.0.1',
        'tags': ['tusharepro']
    }


def plugin_adapt(uri: str) -> bool:
    return uri in FIELDS.keys()


def plugin_capacities() -> list:
    return list(FIELDS.keys())


# ----------------------------------------------------------------------------------------------------------------------

delayer = Delayer(1200)


def __fetch_stock_holder_data(**kwargs) -> pd.DataFrame:
    uri = kwargs.get('uri')
    result = check_execute_test_flag(**kwargs)

    if result is None:
        # period = kwargs.get('due_date')
        ts_code = pickup_ts_code(kwargs)
        # since, until = normalize_time_serial(period, default_since(), today())

        pro = ts.pro_api(config.TS_TOKEN)
        # time_iter = DateTimeIterator(since, until)
        #
        # result = None
        # while not time_iter.end():
        #     # The max items count retrieved per 1 fetching: 1000
        #     # The max items per 1 year: 52 (one new item per 7days for PledgeStatus)
        #     # So the iter years should not be larger than 20 years
        #
        #     sub_since, sub_until = time_iter.iter_years(15)
        #     ts_since = sub_since.strftime('%Y%m%d')
        #     ts_until = sub_until.strftime('%Y%m%d')
        #
        #     clock = Clock()
        #     delayer.delay()
        #     if uri == 'Stockholder.PledgeStatus':
        #         sub_result = pro.pledge_stat(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
        #     elif uri == 'Stockholder.PledgeHistory':
        #         sub_result = pro.pledge_detail(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
        #     else:
        #         sub_result = None
        #     print(uri + ' Network finished, time spending: ' + str(clock.elapsed_ms()) + 'ms')
        #
        #     if sub_result is not None:
        #         if result is None:
        #             result = sub_result
        #         else:
        #             result.append(result)

        clock = Clock()
        delayer.delay()
        if uri == 'Stockholder.PledgeStatus':
            result = pro.pledge_stat(ts_code=ts_code)
        elif uri == 'Stockholder.PledgeHistory':
            result = pro.pledge_detail(ts_code=ts_code)
        else:
            result = None
        print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        result.fillna(0.0)
        if uri == 'Stockholder.PledgeStatus':
            result['due_date'] = result['end_date']
            result['total_share'] = result['total_share'] * 10000
            result['rest_pledge'] = result['rest_pledge'] * 10000
            result['unrest_pledge'] = result['unrest_pledge'] * 10000
            result['pledge_count'] = result['pledge_count'].astype(np.int64)
            result['pledge_ratio'] = result['pledge_ratio'].astype(float)
        elif uri == 'Stockholder.PledgeHistory':
            result['due_date'] = result['ann_date']
            result['pledge_amount'] = result['pledge_amount'] * 10000
            result['holding_amount'] = result['holding_amount'] * 10000
            result['pledged_amount'] = result['pledged_amount'] * 10000

        result['due_date'] = pd.to_datetime(result['due_date'])
        result['stock_identity'] = result['ts_code']
        result['stock_identity'] = result['stock_identity'].str.replace('.SH', '.SSE')
        result['stock_identity'] = result['stock_identity'].str.replace('.SZ', '.SZSE')

    return result


# ----------------------------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri in FIELDS.keys():
        return __fetch_stock_holder_data(**kwargs)
    else:
        return None


def validate(**kwargs) -> bool:
    nop(kwargs)
    return True


def fields() -> dict:
    return FIELDS

