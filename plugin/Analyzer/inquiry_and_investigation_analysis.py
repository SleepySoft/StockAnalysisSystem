import pandas as pd

from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.AnalyzerUtility import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.Database.DatabaseEntry import DatabaseEntry


def analysis_inquiry(securities: str, data_hub: DataHubEntry,
                     database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(database)

    df = data_hub.get_data_center().query('Market.Enquiries', securities)
    if df is None or len(df) == 0:
        return AnalysisResult(securities, AnalysisResult.SCORE_PASS, '四年内无问询记录（也可能是数据缺失）')

    error_report = check_gen_report_when_data_missing(df, securities, 'Market.Enquiries',
                                                      ['stock_identity', 'enquiry_date', 'enquiry_topic'])
    if error_report is not None:
        return error_report

    df_slice = df[df['stock_identity'] == securities]
    df_slice_in_4_years = df_slice[df_slice['enquiry_date'] > years_ago(5)]

    score = 100
    reason = []

    for index, row in df_slice_in_4_years.iterrows():
        enquiry_date = row['enquiry_date']
        enquiry_topic = row['enquiry_topic']
        enquiry_title = row['enquiry_title']
        if '问询函' in enquiry_topic or '关注函' in enquiry_topic:
            score = 59
            reason.append('%s: <<%s>> -- %s' % (date2text(enquiry_date), enquiry_topic, enquiry_title))

    if len(reason) == 0:
        reason.append('近四年无敏感问询')

    return AnalysisResult(securities, score, reason)


def analysis_investigation(securities: str, data_hub: DataHubEntry,
                           database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(database)

    if context.cache.get('investigation', None) is None:
        context.cache['investigation'] = data_hub.get_data_center().query('Market.Investigation')
    df = context.cache.get('investigation', None)

    error_report = check_gen_report_when_data_missing(df, securities, 'Market.Investigation',
                                                      ['stock_identity', 'investigate_date',
                                                       'investigate_topic', 'investigate_reason'])
    if error_report is not None:
        return error_report

    df_slice = df[df['stock_identity'] == securities]
    df_slice_in_4_years = df_slice[df_slice['investigate_date'] > years_ago(5)]

    score = 100
    reason = []

    for index, row in df_slice_in_4_years.iterrows():
        score = 0
        investigate_date = row['investigate_date']
        investigate_topic = row['investigate_topic']
        investigate_reason = row['investigate_reason']
        reason.append('%s: <<%s>> -- %s' % (date2text(investigate_date), investigate_topic, investigate_reason))
    if len(reason) == 0:
        reason.append('近四年无立案调查记录')

    return AnalysisResult(securities, score, reason, AnalysisResult.WEIGHT_ONE_VOTE_VETO)


# ----------------------------------------------------------------------------------------------------------------------

METHOD_LIST = [
    ('b60310bd-cbb4-438f-89c0-ac68b705348d', '交易所问询', '分析该公司近期是否被问询',       analysis_inquiry),
    ('f8f6b993-4cb0-4c93-84fd-8fd975b7977d', '证监会调查', '分析该公司近期是否被立案调查',   analysis_investigation),
]


def plugin_prob() -> dict:
    return {
        'plugin_id': '85a052ba-d7ff-4390-a311-6fd486169ba6',
        'plugin_name': 'basic_finance_analysis',
        'plugin_version': '0.0.0.1',
        'tags': ['finance', 'analyzer'],
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

