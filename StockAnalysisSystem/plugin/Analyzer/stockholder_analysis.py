import pandas as pd

from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.AnalyzerUtility import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.Database.DatabaseEntry import DatabaseEntry


# ------------------------------------------------------ 01 - 05 -------------------------------------------------------

def equity_interest_pledge_too_high(securities: str, data_hub: DataHubEntry,
                                    database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(database)
    nop(context)

    query_fields = ['质押次数', '无限售股质押数量', '限售股份质押数量', '总股本', '质押比例']
    if not data_hub.get_data_center().check_readable_name(query_fields):
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '无法识别的字段名')

    df = data_hub.get_data_center().query('Stockholder.PledgeStatus', securities, (years_ago(2), now()),
                                          fields=query_fields + ['stock_identity', 'due_date'], readable=True)
    if df is None or len(df) == 0:
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '没有数据')
    df = df.sort_values('due_date', ascending=False)

    score = 100
    reason = []
    previous_pledge_times = 0
    for index, row in df.iterrows():
        due_date = row['due_date']

        pledge_rate = row['质押比例']
        pledge_times = row['质押次数']
        if pledge_times != previous_pledge_times:
            if pledge_rate > 50.0:
                score = 0
            if pledge_rate > 20.0:
                score = 60
                reason.append('%s: 质押比例：%.2f%%' % (str(due_date), pledge_rate))
            previous_pledge_times = pledge_times

    if len(reason) == 0:
        reason = '近4年没有超过20%的质押记录'
    return AnalysisResult(securities, score, reason)


def analysis_dispersed_ownership(securities: str, data_hub: DataHubEntry,
                                 database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(database, context)
    df = data_hub.get_data_center().query('Stockholder.Statistics', securities, (years_ago(3), now()),)
    if df is None or len(df) == 0:
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '没有数据')
    df = df[df['period'].dt.month == 12]
    df = df.sort_values('period', ascending=False)

    score = 100
    reason = []
    applied = False
    for index, row in df.iterrows():
        period = row['period']
        stockholder_top10 = row['stockholder_top10']
        stockholder_top10_nt = row['stockholder_top10_nt']

        if not isinstance(stockholder_top10, (list, tuple)):
            continue
        if len(stockholder_top10) != 10:
            continue

        largest_ratio = 0.0
        biggest_holder = ''
        for stockholder_data in stockholder_top10:
            if 'hold_ratio' not in stockholder_data.keys() or 'holder_name' not in stockholder_data.keys():
                break
            applied = True
            hold_ratio = stockholder_data.get('hold_ratio')
            holder_name = stockholder_data.get('holder_name')
            if hold_ratio > largest_ratio:
                largest_ratio = hold_ratio
                biggest_holder = holder_name
        if largest_ratio == 0.0:
            return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED,
                                  '缺少必要数据，请确保数据包含tushare pro数据源')
        if largest_ratio < 0.1:
            score = 0
            reason.append('%s: 最大股东 %s 持股比例为%.2f%%，小于10%%' %
                          (str(period), biggest_holder, largest_ratio * 100))
        else:
            reason.append('%s: 最大股东 %s 持股比例为%.2f%%' %
                          (str(period), biggest_holder, largest_ratio * 100))

    if len(reason) == 0:
        reason.append('没有数据')
    return AnalysisResult(securities, score, reason) if applied else \
        AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, reason)


# ------------------------------------------------------ 05 - 10 -------------------------------------------------------


# ------------------------------------------------------ 11 - 15 -------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------

METHOD_LIST = [
    # 1 - 5
    ('4ccedeea-b731-4b97-9681-d804838e351b', '股权质押过高',    '排除股权质押高于50%的公司',            equity_interest_pledge_too_high),
    ('e515bd4b-db4f-49e2-ac55-1927a28d2a1c', '股权分散',       '排除最大股东持股不足10%的企业',         analysis_dispersed_ownership),
    ('41e20665-4b1b-4423-97de-33764de09e02', '',       '',         None),
    ('1dfe5faa-183c-4b30-aa5f-e0c55e064c31', '',       '',         None),
    ('b646a253-33ec-4313-a5f3-7419363079a8', '',       '',         None),
]


def plugin_prob() -> dict:
    return {
        'plugin_id': 'ad29184c-8a01-4f18-b2a9-60650b2df91a',
        'plugin_name': 'basic_finance_analysis',
        'plugin_version': '0.0.0.1',
        'tags': ['stockholder', 'analyzer'],
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


















