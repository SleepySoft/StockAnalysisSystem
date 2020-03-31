import pandas as pd
from datetime import date

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    import config
    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Utiltity.digit_utility import *
    from Analyzer.AnalyzerUtility import *
    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
except Exception as e:
    sys.path.append(root_path)

    import config
    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Utiltity.digit_utility import *
    from Analyzer.AnalyzerUtility import *
    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------

portrait_score_table = {
    '+++': 40,
    '++-': 100,
    '+-+': 70,
    '+--': 100,

    '-++': 30,
    '-+-': 40,
    '--+': 55,
    '---': 0,
}

portrait_comments_table = {
    '+++': '妖精型：既赚钱，又不投资，还筹资 - 注意投资项目情况',
    '++-': '老母鸡型：如果投资现金非变卖家产所得，且低PE高股息，可考虑吃息',
    '+-+': '蛮牛型：所有收入都花费上扩张上，注意投资项目前景及风险',
    '+--': '奶牛型：以收入覆盖扩张，重点关注其持续性',

    '-++': '骗吃骗喝型：靠投资收入和借债维持生存',
    '-+-': '坐吃山空型：如果靠变卖资产支持，则危险；如果投资收益尚可，且能堵住经营现金缺口则还有希望',
    '--+': '赌徒型：靠借贷为生，投资无收益（或仍继续投资），翻本看运气 - 关注项目前景及管理层品性',
    '---': '大出血型：不参与',
}


def analyzer_stock_portrait(securities: str, data_hub: DataHubEntry,
                            database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(database)

    if context.cache.get('securities_info', None) is None:
        context.cache['securities_info'] = data_hub.get_data_center().query('Market.SecuritiesInfo')
    df_info = context.cache.get('securities_info', None)

    df_slice = df_info[df_info['stock_identity'] == securities]
    industry = get_dataframe_slice_item(df_slice, 'industry', 0, '')
    if industry in ['银行', '保险', '房地产', '全国地产', '区域地产']:
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '不适用于此行业')

    df_balance, result = query_readable_annual_report_pattern(data_hub, 'Finance.BalanceSheet',
                                                              securities, (years_ago(5), now()),
                                                              ['资产总计', '负债合计'])
    if result is not None:
        return result

    df_cash, result = query_readable_annual_report_pattern(data_hub, 'Finance.CashFlowStatement',
                                                           securities, (years_ago(5), now()),
                                                           ['经营活动产生的现金流量净额',
                                                            '投资活动产生的现金流量净额',
                                                            '筹资活动产生的现金流量净额'])
    if result is not None:
        return result

    df = pd.merge(df_balance, df_cash, how='left', on=['stock_identity', 'period'])

    reason = []
    portraits = {}
    for index, row in df.iterrows():
        period = row['period']

        net_assets = row['资产总计'] - row['负债合计']
        if net_assets < 1:
            # No data
            continue

        portrait = \
            ('-' if can_ignore_or_negative(row['经营活动产生的现金流量净额'], net_assets, 0.1) else '+') + \
            ('-' if can_ignore_or_negative(row['投资活动产生的现金流量净额'], net_assets, 0.1) else '+') + \
            ('-' if can_ignore_or_negative(row['筹资活动产生的现金流量净额'], net_assets, 0.1) else '+')
        if portrait in portraits.keys():
            portraits[portrait] += 1
        else:
            portraits[portrait] = 1
        reason.append('%s : %s' % (period.year, portrait))

    portrait_counts = len(portraits)
    if portrait_counts > 0:
        most_portrait = max(portraits, key=lambda key: portraits[key])
        most_portrait_count = portraits[most_portrait]
        if float(most_portrait_count) / portrait_counts >= 0.7:
            return AnalysisResult(securities,
                                  portrait_score_table.get(most_portrait, 0),
                                  portrait_comments_table.get(most_portrait, ''))
        else:
            reason.insert(0, '不稳定的经营，投资及筹资表现')
            return AnalysisResult(securities,
                                  AnalysisResult.SCORE_NOT_APPLIED,
                                  portrait_comments_table.get(most_portrait, ''))
    else:
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '无足够数据')


def analyzer_check_monetary_fund(securities: str, data_hub: DataHubEntry,
                                 database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(database)

    if context.cache.get('securities_info', None) is None:
        context.cache['securities_info'] = data_hub.get_data_center().query('Market.SecuritiesInfo')
    df_info = context.cache.get('securities_info', None)

    df_slice = df_info[df_info['stock_identity'] == securities]
    industry = get_dataframe_slice_item(df_slice, 'industry', 0, '')
    if industry in ['银行', '保险', '房地产', '全国地产', '区域地产']:
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '不适用于此行业')

    fields_balance_sheet = ['货币资金', '资产总计', '负债合计',
                            '短期借款', '一年内到期的非流动负债', '其他流动负债',
                            '长期借款', '应付债券', '其他非流动负债',
                            '应收票据', '流动负债合计',
                            '交易性金融资产', '可供出售金融资产']
    df_balance_sheet, result = query_readable_annual_report_pattern(
        data_hub, 'Finance.BalanceSheet', securities, (years_ago(5), now()), fields_balance_sheet)
    if result is not None:
        return result

    score = []
    reason = []
    for index, row in df_balance_sheet.iterrows():
        period = row['period']

        var = dict(row)

        var['净资产'] = var['资产总计'] - var['负债合计']
        var['短期负债'] = var['短期借款'] + var['一年内到期的非流动负债'] + var['其他流动负债']
        var['有息负债'] = var['短期负债'] + var['长期借款'] + var['应付债券'] + var['其他非流动负债']
        var['金融资产'] = var['交易性金融资产'] + var['可供出售金融资产']

        if var['有息负债'] > 1:
            var['货币资金/有息负债'] = var['货币资金'] / var['有息负债']
            reason.append('%s : 货币资金/有息负债 = %s' % (period.year, format_pct(var['货币资金/有息负债'])))

            if var['货币资金/有息负债'] < 2.0:
                score.append(0)
            elif var['货币资金/有息负债'] < 3.0:
                score.append(60)
            else:
                score.append(100)
        else:
            score.append(100)
            reason.append('%s : 无有息负债' % period.year)

        if var['短期负债'] > 1:
            var['货币资金/短期负债'] = var['货币资金'] / var['短期负债']
            if var['货币资金/短期负债'] < 1.0:
                reason.append('%s : 货币资金/短期负债 = %s, 小于1' % (period.year, format_pct(var['货币资金/短期负债'])))
                score.append(0)
            else:
                score.append(100)
        else:
            score.append(100)
            reason.append('%s : 无短期负债' % period.year)

        var['有息负债/资产总计'] = var['有息负债'] / var['资产总计']
        var['货币资金+金融资产'] = var['货币资金'] + var['金融资产']

        if var['有息负债/资产总计'] > 0.6:
            score.append(0)
            reason.append('%s 有息负债/资产总计 = %s, 大于 60%%' % (period.year, format_pct(var['有息负债/资产总计'])))
        else:
            score.append(100)

        if var['货币资金+金融资产'] < var['有息负债']:
            score.append(0)
            reason.append('%s : 货币资金+金融资产 = %s 小于 有息负债 %s' %
                          (period.year, format_w(var['货币资金+金融资产']), format_w(var['有息负债'])))
        else:
            score.append(100)

    if len(score) > 0:
        return AnalysisResult(securities, int(float(sum(score)) / float(len(score))), reason)
    else:
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '无数据')


def analyzer_check_receivable_and_prepaid(securities: str, data_hub: DataHubEntry,
                                          database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:
    nop(database)

    if context.cache.get('securities_info', None) is None:
        context.cache['securities_info'] = data_hub.get_data_center().query('Market.SecuritiesInfo')
    df_info = context.cache.get('securities_info', None)
    df_slice = df_info[df_info['stock_identity'] == securities]
    industry = get_dataframe_slice_item(df_slice, 'industry', 0, '')
    if industry in ['银行', '保险', '房地产', '全国地产', '区域地产']:
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '不适用于此行业')

    df_income, result = query_readable_annual_report_pattern(data_hub, 'Finance.IncomeStatement',
                                                             securities, (years_ago(5), now()),
                                                             ['营业收入', '营业总收入'])
    if result is not None:
        return result

    fields_balance_sheet = ['应收账款', '应收票据', '其他应收款', '长期应收款', '应收款项']
    df_balance_sheet, result = query_readable_annual_report_pattern(
        data_hub, 'Finance.BalanceSheet', securities, (years_ago(5), now()), fields_balance_sheet)
    if result is not None:
        return result

    df = pd.merge(df_income, df_balance_sheet, how='left', on=['stock_identity', 'period'])
    df = df.sort_values('period')

    score = []
    reason = []
    previous = None
    for index, row in df.iterrows():
        period = row['period']

        var = dict(row)
        var['应收款'] = var['应收账款'] + var['应收票据']

        if var['营业收入'] < 1:
            reason.append('%s : 营业收入为零，可能数据缺失？' % period.year)
            previous = var
            continue

        var['应收款/营业收入'] = var['应收款'] / var['营业收入']
        var['其他应收款/营业收入'] = var['其他应收款'] / var['营业收入']

        if var['应收款/营业收入'] + var['其他应收款/营业收入'] < 0.05 and (
                previous is None or previous['应收款/营业收入'] + previous['其他应收款/营业收入'] < 0.05):
            # Too small
            previous = var
            continue

        if var['应收款/营业收入'] > 0.6:
            score.append(0)
            reason.append('%s : 应收款/营业收入 = %s 大于 60%%' %
                          (period.year, format_pct(var['应收款/营业收入'])))
        else:
            score.append(100)

        if var['其他应收款/营业收入'] > 0.1:
            reason.append('%s : 其他应收款/营业收入 = %s 大于 10%%' %
                          (period.year, format_pct(var['其他应收款/营业收入'])))
            score.append(0)
        else:
            score.append(100)

        if previous is not None:
            # Has previous data
            if previous['应收款'] < 1.0:
                if var['应收款'] > 1.0:
                    score.append(50)
                    reason.append('%s : 应收款从0增长到%s' % (period.year, format_w(var['应收款'])))
            else:
                var['应收增长'] = var['应收款'] / previous['应收款']
                var['营业收入增长'] = var['营业收入'] / previous['营业收入']

                if var['应收增长'] > 10:
                    score.append(50)
                    reason.append('%s : 应收款实然大幅下降超过90%% (%s -> %s)' %
                                  (period.year, previous['应收款'], var['应收款']))
                elif var['应收增长'] < 0.1:
                    score.append(0)
                    reason.append('%s : 应收款实然大幅上升超过10倍 (%s -> %s)' %
                                  (period.year, previous['应收款'], var['应收款']))
                else:
                    score.append(100)

                if var['应收增长'] / var['营业收入增长'] > 2.0:
                    reason.append('%s : 应收增长 = %s 大于 营业收入增长 %s 两倍' %
                                  (period.year, format_pct(var['应收增长']), format_pct(var['营业收入增长'])))
                    score.append(0)
                else:
                    score.append(100)
        previous = var

    if len(score) > 0:
        return AnalysisResult(securities, int(float(sum(score)) / float(len(score))), reason)
    else:
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '无数据')


# ----------------------------------------------------------------------------------------------------------------------

METHOD_LIST = [
    ('3ee3a4ff-a2cf-4244-8f45-c319016ee16b', '[T001] 现金流肖像',    '根据经营现金流,投资现金流,筹资现金流的情况为企业绘制画像',       analyzer_stock_portrait),
    ('7e132f82-a28e-4aa9-aaa6-81fa3692b10c', '[T002] 货币资金分析',  '分析货币资金，详见excel中的对应的ID行',                         analyzer_check_monetary_fund),
    ('7b0478d3-1e15-4bce-800c-6f89ee743600', '[T003] 应收预付分析',  '分析应收款和预付款，详见excel中的对应的ID行',                   analyzer_check_receivable_and_prepaid),
    ('fff6c3cf-a6e5-4fa2-9dce-7d0566b581a1', '', '',       None),
    ('d2ced262-7a03-4428-9220-3d4a2a8fe201', '', '',       None),

    ('bceef7fc-20c5-4c8a-87fc-d5fb7437bc1d', '', '',       None),
    ('9777f5c1-0e79-4e04-9082-1f38891c2922', '', '',       None),
    ('de6b699e-a8d3-47fd-b264-cbddb8dcf5b9', '', '',       None),
    ('8987d858-4157-44bb-948e-0834682132c2', '', '',       None),
    ('a151a2ae-d308-4b9d-aa2a-daddb674ed6d', '', '',       None),
]


def plugin_prob() -> dict:
    return {
        'plugin_id': '0da12555-d18a-4f0c-9bfe-b3903d927aa6',
        'plugin_name': 'analyzer_tang',
        'plugin_version': '0.0.0.1',
        'tags': ['tang', 'analyzer'],
        'methods': METHOD_LIST,
    }


def plugin_adapt(method: str) -> bool:
    return method in methods_from_prob(plugin_prob())


def plugin_capacities() -> list:
    return [
        'score',
        'inclusive',
        'exclusive',
    ]


# ----------------------------------------------------------------------------------------------------------------------

def analysis(securities: [str], methods: [str], data_hub: DataHubEntry,
             database: DatabaseEntry, extra: dict) -> [AnalysisResult]:
    return standard_dispatch_analysis(securities, methods, data_hub, database, extra, METHOD_LIST)




