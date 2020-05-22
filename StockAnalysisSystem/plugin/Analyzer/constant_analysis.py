import pandas as pd

from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.df_utility import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.AnalyzerUtility import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.Database.DatabaseEntry import DatabaseEntry


# ------------------------------------------------------ 01 - 05 -------------------------------------------------------

def analysis_black_list(securities: str, data_hub: DataHubEntry,
                        database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(data_hub)

    if context.cache.get('black_table', None) is None:
        context.cache['black_table'] = database.get_black_table().get_name_table()
    black_table = context.cache.get('black_table', None)

    df_slice = black_table[black_table['name'] == securities]
    exclude = len(df_slice) > 0
    if exclude:
        reason = get_dataframe_slice_item(df_slice, 'reason', 0, '')
    else:
        reason = '不在黑名单中'
    return AnalysisResult(securities, not exclude, reason)


def analysis_less_than_3_years(securities: str, data_hub: DataHubEntry,
                               database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(database)

    if context.cache.get('securities_info', None) is None:
        context.cache['securities_info'] = data_hub.get_data_center().query('Market.SecuritiesInfo')
    df = context.cache.get('securities_info', None)

    df_slice = df[df['stock_identity'] == securities]
    listing_date = get_dataframe_slice_item(df_slice, 'listing_date', 0, now())
    exclude = now().year - listing_date.year < 3
    reason = '上市日期' + str(listing_date) + ('小于三年' if exclude else '大于三年')
    return AnalysisResult(securities, not exclude, reason)


def analysis_location_limitation(securities: str, data_hub: DataHubEntry,
                                 database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(database)

    if context.cache.get('securities_info', None) is None:
        context.cache['securities_info'] = data_hub.get_data_center().query('Market.SecuritiesInfo')
    df = context.cache.get('securities_info', None)

    df_slice = df[df['stock_identity'] == securities]
    area = get_dataframe_slice_item(df_slice, 'area', 0, '')
    exclude = area in ['黑龙江', '辽宁', '吉林']
    reason = securities + '地域为' + str(area)
    return AnalysisResult(securities, not exclude, reason)


def analysis_exclude_industries(securities: str, data_hub: DataHubEntry,
                                database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(database)

    if context.cache.get('securities_info', None) is None:
        context.cache['securities_info'] = data_hub.get_data_center().query('Market.SecuritiesInfo')
    df = context.cache.get('securities_info', None)

    df_slice = df[df['stock_identity'] == securities]

    industry = get_dataframe_slice_item(df_slice, 'industry', 0, '')
    exclude = industry in ['种植业', '渔业', '林业', '畜禽养殖', '农业综合']
    reason = '所在行业[' + str(industry) + (']属于农林牧渔' if exclude else ']不属于农林牧渔')
    return AnalysisResult(securities, not exclude, reason)


# ------------------------------------------------------ 05 - 10 -------------------------------------------------------


# ------------------------------------------------------ 11 - 15 -------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------

METHOD_LIST = [
    # 1 - 5
    ('7a2c2ce7-9060-4c1c-bca7-71ca12e92b09', '黑名单',       '排除黑名单中的股票',         analysis_black_list),
    ('e639a8f1-f2f5-4d48-a348-ad12508b0dbb', '不足三年',     '排除上市不足三年的公司',     analysis_less_than_3_years),
    ('f39f14d6-b417-4a6e-bd2c-74824a154fc0', '地域限制',     '排除特定地域的公司',         analysis_location_limitation),
    ('1fdee036-c7c1-4876-912a-8ce1d7dd978b', '农林牧渔',     '排除农林牧渔相关行业',       analysis_exclude_industries),
]


def plugin_prob() -> dict:
    return {
        'plugin_id': '01a7acb0-19e9-41af-9629-eaa4ccfe785f',
        'plugin_name': 'constant_analysis',
        'plugin_version': '0.0.0.1',
        'tags': ['constant', 'analyzer'],
        'methods': METHOD_LIST,
    }


def plugin_adapt(method: str) -> bool:
    return method in methods_from_prob(plugin_prob())


def plugin_capacities() -> list:
    return [
        'exclusive',
    ]


# ----------------------------------------------------------------------------------------------------------------------

def analysis(securities: [str], methods: [str], data_hub: DataHubEntry,
             database: DatabaseEntry, extra: dict) -> [AnalysisResult]:
    return standard_dispatch_analysis(securities, methods, data_hub, database, extra, METHOD_LIST)






