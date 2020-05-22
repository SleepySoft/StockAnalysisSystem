import pandas as pd
import tushare as ts

from StockAnalysisSystem.core.config import TS_TOKEN
from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.CollectorUtility import *


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
    'Stockholder.Statistics': {

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

        pro = ts.pro_api(TS_TOKEN)
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


# stk_holdernumber() : 100 times per 1 min
delayer_stock_holder_statistics = Delayer(600)


def __fetch_stock_holder_statistics_piece(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    result = check_execute_test_flag(**kwargs)

    if result is None:
        period = kwargs.get('period')
        ts_code = pickup_ts_code(kwargs)
        since, until = normalize_time_serial(period, default_since(), today())

        since_limit = years_ago_of(until, 3)
        since = max([since, since_limit])

        clock = Clock()
        pro = ts.pro_api(TS_TOKEN)

        ts_since = since.strftime('%Y%m%d')
        ts_until = until.strftime('%Y%m%d')

        delayer_stock_holder_statistics.delay()
        result_count = pro.stk_holdernumber(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
        result_top10 = pro.top10_holders(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
        result_top10_nt = pro.top10_floatholders(ts_code=ts_code, start_date=ts_since, end_date=ts_until)

        # 002978.SZ
        # 20070518 - 20200517
        # top10_floatholders() may get empty DataFrame
        print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

        if result_top10 is not None and len(result_top10) > 0:
            del result_top10['ts_code']
            del result_top10['ann_date']

            result_top10.fillna(0.0)
            result_top10['hold_ratio'] = result_top10['hold_ratio'] / 100

            result_top10_grouped = pd.DataFrame({'stockholder_top10': result_top10.groupby('end_date').apply(
                lambda x: x.drop('end_date', axis=1).to_dict('records'))}).reset_index()
        else:
            result_top10_grouped = None

        if result_top10_nt is not None and len(result_top10_nt) > 0:
            del result_top10_nt['ts_code']
            del result_top10_nt['ann_date']

            result_top10_nt_grouped = pd.DataFrame({'stockholder_top10_nt': result_top10_nt.groupby('end_date').apply(
                lambda x: x.drop('end_date', axis=1).to_dict('records'))}).reset_index()
        else:
            result_top10_nt_grouped = None

        if result_count is None or result_top10 is None or result_top10_nt is None:
            print('Fetch stockholder statistics data fail.')
            return None

        result = result_top10_grouped \
            if result_top10_grouped is not None and len(result_top10_grouped) > 0 else None
        result = pd.merge(result, result_top10_nt_grouped, how='outer', on='end_date', sort=False) \
            if result is not None else result_top10_nt_grouped
        result = pd.merge(result, result_count, how='left', on='end_date', sort=False) \
            if result is not None else result_count
        result['ts_code'] = ts_code

        # del result_top10['ts_code']
        # del result_top10['ann_date']
        # del result_top10_nt['ts_code']
        # del result_top10_nt['ann_date']
        #
        # result_top10.fillna(0.0)
        # result_top10['hold_ratio'] = result_top10['hold_ratio'] / 100
        #
        # try:
        #     result_top10_grouped = pd.DataFrame({'stockholder_top10': result_top10.groupby('end_date').apply(
        #         lambda x: x.drop('end_date', axis=1).to_dict('records'))}).reset_index()
        #     result_top10_nt_grouped = pd.DataFrame({'stockholder_top10_nt': result_top10_nt.groupby('end_date').apply(
        #         lambda x: x.drop('end_date', axis=1).to_dict('records'))}).reset_index()
        #
        #     result = pd.merge(result_top10_grouped, result_top10_nt_grouped, how='outer', on='end_date', sort=False)
        #     result = pd.merge(result, result_count, how='left', on='end_date', sort=False)
        #     result['ts_code'] = ts_code
        # except Exception as e:
        #     print('Fetching stockholder data error:')
        #     print(e)
        #     print(traceback.format_exc())
        # finally:
        #     pass

        # Ts data may have issues, just detect it.
        for index, row in result.iterrows():
            end_date = row['end_date']
            stockholder_top10 = row['stockholder_top10']
            stockholder_top10_nt = row['stockholder_top10_nt']

            if isinstance(stockholder_top10, list):
                if len(stockholder_top10) != 10:
                    print('%s: stockholder_top10 length is %s' % (end_date, len(stockholder_top10)))
            else:
                print('%s: stockholder_top10 type error %s' % (end_date, str(stockholder_top10)))

            if isinstance(stockholder_top10_nt, list):
                if len(stockholder_top10_nt) != 10:
                    print('%s: stockholder_top10_nt length is %s' % (end_date, len(stockholder_top10_nt)))
            else:
                print('%s: stockholder_top10 type error %s' % (end_date, str(stockholder_top10_nt)))

    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        result.fillna('')
        result['period'] = pd.to_datetime(result['end_date'])
        result['stock_identity'] = result['ts_code']
        result['stock_identity'] = result['stock_identity'].str.replace('.SH', '.SSE')
        result['stock_identity'] = result['stock_identity'].str.replace('.SZ', '.SZSE')

    return result


# This method can fetch the whole data from 1990 to now, but it takes too much of time (50s for 000001)
def __fetch_stock_holder_statistics_full(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    result = check_execute_test_flag(**kwargs)

    if result is None:
        period = kwargs.get('period')
        ts_code = pickup_ts_code(kwargs)
        since, until = normalize_time_serial(period, default_since(), today())

        clock = Clock()
        pro = ts.pro_api(TS_TOKEN)
        time_iter = DateTimeIterator(since, until)

        ts_since = since.strftime('%Y%m%d')
        ts_until = until.strftime('%Y%m%d')
        result_count = pro.stk_holdernumber(ts_code=ts_code, start_date=ts_since, end_date=ts_until)

        result_top10 = None
        result_top10_nt = None
        while not time_iter.end():
            # Top10 api can only fetch 100 items per one time (100 / 10 / 4 = 2.5Years)
            sub_since, sub_until = time_iter.iter_years(2.4)
            ts_since = sub_since.strftime('%Y%m%d')
            ts_until = sub_until.strftime('%Y%m%d')
            delayer.delay()

            result_top10_part = pro.top10_holders(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
            result_top10_nt_part = pro.top10_floatholders(ts_code=ts_code, start_date=ts_since, end_date=ts_until)

            result_top10 = pd.concat([result_top10, result_top10_part])
            result_top10_nt = pd.concat([result_top10_nt, result_top10_nt_part])

        print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

        if result_count is None or result_top10 is None or result_top10_nt is None:
            print('Fetch stockholder statistics data fail.')
            return None

        del result_top10['ann_date']
        del result_top10_nt['ann_date']

        key_columns = ['ts_code', 'end_date']
        result_top10_grouped = pd.DataFrame({'stockholder_top10': result_top10.groupby(key_columns).apply(
            lambda x: x.drop(key_columns, axis=1).to_dict('records'))}).reset_index()
        result_top10_nt_grouped = pd.DataFrame({'stockholder_top10_nt': result_top10_nt.groupby(key_columns).apply(
            lambda x: x.drop(key_columns, axis=1).to_dict('records'))}).reset_index()

        result = pd.merge(result_top10_grouped, result_top10_nt_grouped, how='outer', on=key_columns, sort=False)
        result = pd.merge(result, result_count, how='outer', on=key_columns, sort=False)

        print(result)

    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        result.fillna('')
        result['period'] = pd.to_datetime(result['end_date'])
        result['stock_identity'] = result['ts_code']
        result['stock_identity'] = result['stock_identity'].str.replace('.SH', '.SSE')
        result['stock_identity'] = result['stock_identity'].str.replace('.SZ', '.SZSE')

    return result


# ----------------------------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri in ['Stockholder.PledgeStatus', 'Stockholder.PledgeHistory']:
        return __fetch_stock_holder_data(**kwargs)
    if uri in ['Stockholder.Statistics']:
        return __fetch_stock_holder_statistics_piece(**kwargs)
    return None


def validate(**kwargs) -> bool:
    nop(kwargs)
    return True


def fields() -> dict:
    return FIELDS

