import pandas as pd
import tushare as ts

from StockAnalysisSystem.core.config import TS_TOKEN
from StockAnalysisSystem.core.Utility.common import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.Utility.CollectorUtility import *


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
    'Stockholder.Count': {
        'holder_num': '股东户数',
    },
    'Stockholder.Statistics': {
        'holder_name': '股东名称',
        'hold_amount': '持有数量（股）',
        'hold_ratio': '持有比例',
    },
    'Stockholder.ReductionIncrease': {
        'ts_code':                       'TS代码',
        'ann_date':                      '公告日期',
        'holder_name':                   '股东名称',
        'holder_type':                   '股东类型',                           # G高管P个人C公司
        'in_de':                         '增减持类型',                          # IN增持DE减持
        'change_vol':                    '变动数量',
        'change_ratio':                  '占流通比例',                          # （%）
        'after_share':                   '变动后持股',
        'after_ratio':                   '变动后占流通比例',                       # （%）
        'avg_price':                     '平均价格',
        'total_share':                   '持股总数',
        'begin_date':                    '增减持开始日期',
        'close_date':                    '增减持结束日期',
    }
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

# pledge_stat: https://tushare.pro/document/2?doc_id=110
# pledge_detail: https://tushare.pro/document/2?doc_id=111

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

        if not str_available(ts_code):
            result = None
        else:
            clock = Clock()
            if uri == 'Stockholder.PledgeStatus':
                ts_delay('pledge_stat')
                result = pro.pledge_stat(ts_code=ts_code)
            elif uri == 'Stockholder.PledgeHistory':
                ts_delay('pledge_detail')
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

        convert_ts_code_field(result)
        convert_ts_date_field(result, 'due_date')

        # result['due_date'] = pd.to_datetime(result['due_date'])
        # result['stock_identity'] = result['ts_code']
        # result['stock_identity'] = result['stock_identity'].str.replace('.SH', '.SSE')
        # result['stock_identity'] = result['stock_identity'].str.replace('.SZ', '.SZSE')

    return result


# stk_holdernumber: https://tushare.pro/document/2?doc_id=166

def __fetch_stock_holder_count(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    result = check_execute_test_flag(**kwargs)

    if result is None:
        period = kwargs.get('period')
        ts_code = pickup_ts_code(kwargs)
        since, until = normalize_time_serial(period, default_since(), today())

        pro = ts.pro_api(TS_TOKEN)

        ts_since = since.strftime('%Y%m%d')
        ts_until = until.strftime('%Y%m%d')

        if is_slice_update(ts_code, since, until):
            result = None
        else:
            ts_delay('stk_holdernumber')

            clock = Clock()
            result = pro.stk_holdernumber(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
            print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

            convert_ts_code_field(result)
            convert_ts_date_field(result, 'ann_date')
            convert_ts_date_field(result, 'end_date', 'period')

    check_execute_dump_flag(result, **kwargs)

    return result


# top10_holders: https://tushare.pro/document/2?doc_id=61
# top10_floatholders: https://tushare.pro/document/2?doc_id=62

def __fetch_stock_holder_statistics(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    result = check_execute_test_flag(**kwargs)

    if result is None:
        period = kwargs.get('period')
        ts_code = pickup_ts_code(kwargs)
        since, until = normalize_time_serial(period, default_since(), today())

        # See TushareApi.xlsx
        # since_limit = years_ago_of(until, 3)
        # since = max([since, since_limit])

        pro = ts.pro_api(TS_TOKEN)

        ts_since = since.strftime('%Y%m%d')
        ts_until = until.strftime('%Y%m%d')

        if is_slice_update(ts_code, since, until):
            result = None
        else:
            clock = Clock()
    
            ts_delay('top10_holders')
            result_top10 = pro.top10_holders(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
    
            ts_delay('top10_floatholders')
            result_top10_float = pro.top10_floatholders(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
    
            print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

            # Process top10_holders data

            del result_top10['ts_code']
            convert_ts_date_field(result_top10, 'ann_date')
            convert_ts_date_field(result_top10, 'end_date')
            result_top10 = result_top10.fillna('')
            grouped_stockholder_top_10 = result_top10.groupby('end_date')
    
            data_dict = {'period': [], 'stockholder_top10': []}
            for g, df in grouped_stockholder_top_10:
                data_dict['period'].append(g)
                del df['end_date']
                data_dict['stockholder_top10'].append(df.to_dict('records'))
            grouped_stockholder_top_10_df = pd.DataFrame(data_dict)
            grouped_stockholder_top_10_df['stock_identity'] = ts_code_to_stock_identity(ts_code)

            # Process top10_floatholders data

            del result_top10_float['ts_code']
            convert_ts_date_field(result_top10_float, 'ann_date')
            convert_ts_date_field(result_top10_float, 'end_date')
            result_top10_float = result_top10_float.fillna('')
            grouped_stockholder_top_10_float = result_top10_float.groupby('end_date')
    
            data_dict = {'period': [], 'stockholder_top10_float': []}
            for g, df in grouped_stockholder_top_10_float:
                data_dict['period'].append(g)
                del df['end_date']
                data_dict['stockholder_top10_float'].append(df.to_dict('records'))
            grouped_stockholder_top_10_float_df = pd.DataFrame(data_dict)
            grouped_stockholder_top_10_float_df['stock_identity'] = ts_code_to_stock_identity(ts_code)

            # Merge together
    
            result = pd.merge(grouped_stockholder_top_10_df, grouped_stockholder_top_10_float_df,
                              on=['stock_identity', 'period'], how='outer')
            result = result.sort_values('period')

        # 002978.SZ
        # 20070518 - 20200517
        # top10_floatholders() may get empty DataFrame
        
        # if isinstance(result_top10, pd.DataFrame) and not result_top10.empty:
        #     del result_top10['ts_code']
        #     del result_top10['ann_date']
        # 
        #     result_top10.fillna(0.0)
        #     result_top10['hold_ratio'] = result_top10['hold_ratio'] / 100
        # 
        #     result_top10_grouped = pd.DataFrame({'stockholder_top10': result_top10.groupby('end_date').apply(
        #         lambda x: x.drop('end_date', axis=1).to_dict('records'))}).reset_index()
        # else:
        #     result_top10_grouped = None
        # 
        # if result_top10_float is not None and len(result_top10_float) > 0:
        #     del result_top10_float['ts_code']
        #     del result_top10_float['ann_date']
        # 
        #     result_top10_float_grouped = pd.DataFrame({'stockholder_top10_nt': result_top10_float.groupby('end_date').apply(
        #         lambda x: x.drop('end_date', axis=1).to_dict('records'))}).reset_index()
        # else:
        #     result_top10_float_grouped = None
        # 
        # if result_count is None or result_top10 is None or result_top10_float is None:
        #     print('Fetch stockholder statistics data fail.')
        #     return None
        # 
        # result = result_top10_grouped \
        #     if result_top10_grouped is not None and len(result_top10_grouped) > 0 else None
        # result = pd.merge(result, result_top10_float_grouped, how='outer', on='end_date', sort=False) \
        #     if result is not None else result_top10_float_grouped
        # result = pd.merge(result, result_count, how='left', on='end_date', sort=False) \
        #     if result is not None else result_count
        # result['ts_code'] = ts_code

        # del result_top10['ts_code']
        # del result_top10['ann_date']
        # del result_top10_float['ts_code']
        # del result_top10_float['ann_date']
        #
        # result_top10.fillna(0.0)
        # result_top10['hold_ratio'] = result_top10['hold_ratio'] / 100
        #
        # try:
        #     result_top10_grouped = pd.DataFrame({'stockholder_top10': result_top10.groupby('end_date').apply(
        #         lambda x: x.drop('end_date', axis=1).to_dict('records'))}).reset_index()
        #     result_top10_float_grouped = pd.DataFrame({'stockholder_top10_nt': result_top10_float.groupby('end_date').apply(
        #         lambda x: x.drop('end_date', axis=1).to_dict('records'))}).reset_index()
        #
        #     result = pd.merge(result_top10_grouped, result_top10_float_grouped, how='outer', on='end_date', sort=False)
        #     result = pd.merge(result, result_count, how='left', on='end_date', sort=False)
        #     result['ts_code'] = ts_code
        # except Exception as e:
        #     print('Fetching stockholder data error:')
        #     print(e)
        #     print(traceback.format_exc())
        # finally:
        #     pass

        # # Ts data may have issues, just detect it.
        # for index, row in result.iterrows():
        #     end_date = row['end_date']
        #     stockholder_top10 = row['stockholder_top10']
        #     stockholder_top10_nt = row['stockholder_top10_nt']
        # 
        #     if isinstance(stockholder_top10, list):
        #         if len(stockholder_top10) != 10:
        #             print('%s: stockholder_top10 length is %s' % (end_date, len(stockholder_top10)))
        #     else:
        #         print('%s: stockholder_top10 type error %s' % (end_date, str(stockholder_top10)))
        # 
        #     if isinstance(stockholder_top10_nt, list):
        #         if len(stockholder_top10_nt) != 10:
        #             print('%s: stockholder_top10_nt length is %s' % (end_date, len(stockholder_top10_nt)))
        #     else:
        #         print('%s: stockholder_top10 type error %s' % (end_date, str(stockholder_top10_nt)))

    check_execute_dump_flag(result, **kwargs)

    # if result is not None:
    #     result.fillna('')
    #     result['period'] = pd.to_datetime(result['end_date'])
    #     result['stock_identity'] = result['ts_code']
    #     result['stock_identity'] = result['stock_identity'].str.replace('.SH', '.SSE')
    #     result['stock_identity'] = result['stock_identity'].str.replace('.SZ', '.SZSE')

    return result


# # This method can fetch the whole data from 1990 to now, but it takes too much of time (50s for 000001)
# def __fetch_stock_holder_statistics_full(**kwargs) -> pd.DataFrame or None:
#     uri = kwargs.get('uri')
#     result = check_execute_test_flag(**kwargs)
#
#     if result is None:
#         period = kwargs.get('period')
#         ts_code = pickup_ts_code(kwargs)
#         since, until = normalize_time_serial(period, default_since(), today())
#
#         clock = Clock()
#         pro = ts.pro_api(TS_TOKEN)
#         time_iter = DateTimeIterator(since, until)
#
#         ts_since = since.strftime('%Y%m%d')
#         ts_until = until.strftime('%Y%m%d')
#         result_count = pro.stk_holdernumber(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
#
#         result_top10 = None
#         result_top10_float = None
#         while not time_iter.end():
#             # Top10 api can only fetch 100 items per one time (100 / 10 / 4 = 2.5Years)
#             sub_since, sub_until = time_iter.iter_years(2.4)
#             ts_since = sub_since.strftime('%Y%m%d')
#             ts_until = sub_until.strftime('%Y%m%d')
#
#             ts_delay('top10_holders')
#             result_top10_part = pro.top10_holders(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
#
#             ts_delay('top10_floatholders')
#             result_top10_float_part = pro.top10_floatholders(ts_code=ts_code, start_date=ts_since, end_date=ts_until)
#
#             result_top10 = pd.concat([result_top10, result_top10_part])
#             result_top10_float = pd.concat([result_top10_float, result_top10_float_part])
#
#         print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))
#
#         if result_count is None or result_top10 is None or result_top10_float is None:
#             print('Fetch stockholder statistics data fail.')
#             return None
#
#         del result_top10['ann_date']
#         del result_top10_float['ann_date']
#
#         key_columns = ['ts_code', 'end_date']
#         result_top10_grouped = pd.DataFrame({'stockholder_top10': result_top10.groupby(key_columns).apply(
#             lambda x: x.drop(key_columns, axis=1).to_dict('records'))}).reset_index()
#         result_top10_float_grouped = pd.DataFrame({'stockholder_top10_nt': result_top10_float.groupby(key_columns).apply(
#             lambda x: x.drop(key_columns, axis=1).to_dict('records'))}).reset_index()
#
#         result = pd.merge(result_top10_grouped, result_top10_float_grouped, how='outer', on=key_columns, sort=False)
#         result = pd.merge(result, result_count, how='outer', on=key_columns, sort=False)
#
#         print(result)
#
#     check_execute_dump_flag(result, **kwargs)
#
#     if result is not None:
#         result.fillna('')
#         result['period'] = pd.to_datetime(result['end_date'])
#         result['stock_identity'] = result['ts_code']
#         result['stock_identity'] = result['stock_identity'].str.replace('.SH', '.SSE')
#         result['stock_identity'] = result['stock_identity'].str.replace('.SZ', '.SZSE')
#
#     return result


# stk_holdertrade: https://tushare.pro/document/2?doc_id=175

def __fetch_stock_holder_reduction_increase_full(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    result = check_execute_test_flag(**kwargs)

    if result is None:
        period = kwargs.get('ann_date')
        ts_code = pickup_ts_code(kwargs)
        since, until = normalize_time_serial(period, default_since(), today())

        pro = ts.pro_api(TS_TOKEN)
        ts_since = since.strftime('%Y%m%d')
        ts_until = until.strftime('%Y%m%d')

        clock = Clock()
        if is_slice_update(ts_code, since, until):
            result = pro.stk_holdertrade(ann_date=ts_since,
                                         fields=list(FIELDS['Stockholder.ReductionIncrease'].keys()))
        else:
            pass
            ts_delay('stk_holdertrade')
            # If not specify fields, begin_date and close_date will be missing.
            result = pro.stk_holdertrade(ts_code=ts_code, start_date=ts_since, end_date=ts_until,
                                         fields=list(FIELDS['Stockholder.ReductionIncrease'].keys()))

        print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))

    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        result.reindex()
        convert_ts_code_field(result)
        convert_ts_date_field(result, 'ann_date')
        result['stock_holder'] = result['holder_name']
        result = result.fillna('')

        if len(result) >= 2000:
            print('Stock %s has more than 2000 sotck trade record.' % ts_code)

        # result['stock_identity'] = result['ts_code'].apply(ts_code_to_stock_identity)
        # result['ann_date'] = pd.to_datetime(result['ann_date'])
        # result['stock_holder'] = result['holder_name']
        # del result['holder_name']

    return result


# ----------------------------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri in ['Stockholder.PledgeStatus', 'Stockholder.PledgeHistory']:
        return __fetch_stock_holder_data(**kwargs)
    if uri in ['Stockholder.Count']:
        return __fetch_stock_holder_count(**kwargs)
    if uri in ['Stockholder.Statistics']:
        return __fetch_stock_holder_statistics(**kwargs)
    if uri in ['Stockholder.ReductionIncrease']:
        return __fetch_stock_holder_reduction_increase_full(**kwargs)
    return None


def validate(**kwargs) -> bool:
    nop(kwargs)
    return True


def fields() -> dict:
    return FIELDS

