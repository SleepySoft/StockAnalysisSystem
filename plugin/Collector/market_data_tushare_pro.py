import pandas as pd
import tushare as ts

from StockAnalysisSystem.core.config import TS_TOKEN
from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.CollectorUtility import *


# ------------------------------------------------------- Fields -------------------------------------------------------

FIELDS = {
    'Market.SecuritiesInfo': {
        'ts_code':                       'TS代码',
        'symbol':                        '股票代码',
        'name':                          '股票名称',
        'area':                          '所在地域',
        'industry':                      '所属行业',
        'fullname':                      '股票全称',
        'enname':                        '英文全称',
        'market':                        '市场类型',                           # 主板/中小板/创业板/科创板
        'exchange':                      '交易所代码',
        'curr_type':                     '交易货币',
        'list_status':                   '上市状态',                           # L上市;D退市;P暂停上市
        'list_date':                     '上市日期',
        'delist_date':                   '退市日期',
        'is_hs':                         '是否沪深港通标的',                       # N否;H沪股通;S深股通
    },
    'Market.IndexInfo': {
        'ts_code':                       'TS代码',
        'name':                          '简称',
        'fullname':                      '指数全称',
        'market':                        '市场',
        'publisher':                     '发布方',
        'index_type':                    '指数风格',
        'category':                      '指数类别',
        'base_date':                     '基期',
        'base_point':                    '基点',
        'list_date':                     '发布日期',
        'weight_rule':                   '加权方式',
        'desc':                          '描述',
        'exp_date':                      '终止日期',
    },
    'Market.TradeCalender': {
        'exchange':                      '交易所',                            # SSE上交所;SZSE深交所
        'cal_date':                      '日历日期',
        'is_open':                       '是否交易',                           # 0休市;1交易
        'pretrade_date':                 '上一个交易日',
    },
    'Market.NamingHistory': {
        'ts_code':                       'TS代码',
        'name':                          '证券名称',
        'start_date':                    '开始日期',
        'end_date':                      '结束日期',
        'ann_date':                      '公告日期',
        'change_reason':                 '变更原因',
    },
    'Market.IndexComponent': {
        'ts_code':                       'TS代码',
        'symbol':                        '股票代码',
        'name':                          '股票名称',
        'area':                          '所在地域',
        'industry':                      '所属行业',
        'fullname':                      '股票全称',
        'enname':                        '英文全称',
        'market':                        '市场类型',                           # 主板/中小板/创业板/科创板
        'exchange':                      '交易所代码',
        'curr_type':                     '交易货币',
        'list_status':                   '上市状态',                           # L上市;D退市;P暂停上市
        'list_date':                     '上市日期',
        'delist_date':                   '退市日期',
        'is_hs':                         '是否沪深港通标的',                       # N否;H沪股通;S深股通
    },
    'Market.SecuritiesTags': {
    },
}


# -------------------------------------------------------- Prob --------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_name': 'market_data_tushare_pro',
        'plugin_version': '0.0.0.1',
        'tags': ['tusharepro']
    }


def plugin_adapt(uri: str) -> bool:
    return uri in FIELDS.keys()


def plugin_capacities() -> list:
    return list(FIELDS.keys())


# ----------------------------------------------------------------------------------------------------------------------

def __fetch_securities_info(**kwargs) -> pd.DataFrame or None:
    result = check_execute_test_flag(**kwargs)
    if result is None:
        pro = ts.pro_api(TS_TOKEN)
        # If we specify the exchange parameter, it raises error.
        result = pro.stock_basic(fields=list(FIELDS.get('Market.SecuritiesInfo').keys()))
    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        result['list_date'] = pd.to_datetime(result['list_date'], format='%Y-%m-%d')
        result['delist_date'] = pd.to_datetime(result['delist_date'], format='%Y-%m-%d')

        result['listing_date'] = pd.to_datetime(result['list_date'], format='%Y-%m-%d')

        if 'code' not in result.columns:
            result['code'] = result['ts_code'].apply(lambda val: val.split('.')[0])
        if 'exchange' not in result.columns:
            result['exchange'] = result['ts_code'].apply(lambda val: val.split('.')[1])
            result['exchange'] = result['exchange'].apply(lambda val: 'SSE' if val == 'SH' else val)
            result['exchange'] = result['exchange'].apply(lambda val: 'SZSE' if val == 'SZ' else val)
        result['stock_identity'] = result['code'] + '.' + result['exchange']

    return result


def __fetch_stock_concept(**kwargs) -> pd.DataFrame or None:
    result = check_execute_test_flag(**kwargs)
    if result is None:
        ts_code = pickup_ts_code(kwargs)
        pro = ts.pro_api(TS_TOKEN)
        result = pro.concept_detail(ts_code=ts_code, fields=[
            'id', 'concept_name', 'ts_code', 'name', 'in_date', 'out_date'])
    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        del result['ts_code']
        result['ts_concept'] = result.to_dict('records')
        result['stock_identity'] = ts_code_to_stock_identity(ts_code)
    return result


def __fetch_indexes_info(**kwargs) -> pd.DataFrame or None:
    SUPPORT_MARKETS = ['SSE', 'SZSE', 'CSI', 'CICC', 'SW', 'MSCI', 'OTH']

    result = check_execute_test_flag(**kwargs)
    if result is None:
        pro = ts.pro_api(TS_TOKEN)

        result = None
        for market in SUPPORT_MARKETS:
            sub_result = pro.index_basic(market=market, fields=list(FIELDS.get('Market.IndexInfo').keys()))
            result = pd.concat([result, sub_result])

    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        result['exchange'] = result['market']
        result['code'] = result['ts_code'].apply(lambda val: val.split('.')[0])
        result['listing_date'] = pd.to_datetime(result['list_date'], format='%Y-%m-%d')
        result['index_identity'] = result['code'].astype(str) + '.' + result['exchange']

    return result


def __fetch_trade_calender(**kwargs) -> pd.DataFrame or None:
    exchange = kwargs.get('exchange', '')
    if str_available(exchange) and exchange not in ['SSE', 'SZSE', 'A-SHARE']:
        return None

    result = check_execute_test_flag(**kwargs)
    if result is None:
        time_serial = kwargs.get('trade_date', None)
        since, until = normalize_time_serial(time_serial, default_since(), today())

        ts_since = since.strftime('%Y%m%d')
        ts_until = until.strftime('%Y%m%d')

        pro = ts.pro_api(TS_TOKEN)
        # If we specify the exchange parameter, it raises error.
        result = pro.trade_cal('', start_date=ts_since, end_date=ts_until)
    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        result.rename(columns={'exchange': 'exchange', 'cal_date': 'trade_date', 'is_open': 'status'}, inplace=True)
        # Because tushare only support SSE and they are the same
        if exchange == 'SZSE' or exchange == 'A-SHARE':
            result.drop(result[result.exchange != 'SSE'].index, inplace=True)
            result['exchange'] = exchange
        else:
            result.drop(result[result.exchange != exchange].index, inplace=True)
        result['trade_date'] = pd.to_datetime(result['trade_date'])
    return result


def __fetch_naming_history(**kwargs):
    result = check_execute_test_flag(**kwargs)
    if result is None:
        ts_code = pickup_ts_code(kwargs)
        period = kwargs.get('naming_date')
        since, until = normalize_time_serial(period, default_since(), today())

        ts_since = since.strftime('%Y%m%d')
        ts_until = until.strftime('%Y%m%d')

        pro = ts.pro_api(TS_TOKEN)
        result = pro.namechange(ts_code=ts_code, start_date=ts_since, end_date=ts_until,
                                fields='ts_code,name,start_date,end_date,ann_date,change_reason')
    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        if 'start_date' in result.columns:
            result['naming_date'] = pd.to_datetime(result['start_date'], format='%Y-%m-%d')
        if 'stock_identity' not in result.columns:
            result['stock_identity'] = result['ts_code'].apply(ts_code_to_stock_identity)

    return result


# ----------------------------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri == 'Market.SecuritiesInfo':
        return __fetch_securities_info(**kwargs)
    elif uri == 'Market.IndexInfo':
        return __fetch_indexes_info(**kwargs)
    elif uri == 'Market.TradeCalender':
        return __fetch_trade_calender(**kwargs)
    elif uri == 'Market.NamingHistory':
        return __fetch_naming_history(**kwargs)
    elif uri == 'Market.IndexComponent':
        return None
    elif uri == 'Market.SecuritiesTags':
        return __fetch_stock_concept(**kwargs)
    else:
        return None


def validate(**kwargs) -> bool:
    nop(kwargs)
    return True


def fields() -> dict:
    return FIELDS



