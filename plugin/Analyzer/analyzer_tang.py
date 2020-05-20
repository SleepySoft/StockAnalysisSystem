import pandas as pd

from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.df_utility import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.digit_utility import *
from StockAnalysisSystem.core.Utiltity.AnalyzerUtility import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.Database.DatabaseEntry import DatabaseEntry


# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------- 现金流画像 -----------------------------------------------------
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

    if check_industry_in(securities, ['银行', '保险', '房地产', '全国地产', '区域地产'], data_hub, database, context):
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


# ----------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------- 货币资金分析 ----------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

def analyzer_check_monetary_fund(securities: str, data_hub: DataHubEntry,
                                 database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:

    if check_industry_in(securities, ['银行', '保险', '房地产', '全国地产', '区域地产'], data_hub, database, context):
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

    df = df_balance_sheet

    df['净资产'] = df['资产总计'] - df['负债合计']
    df['短期负债'] = df['短期借款'] + df['一年内到期的非流动负债'] + df['其他流动负债']
    df['有息负债'] = df['短期负债'] + df['长期借款'] + df['应付债券'] + df['其他非流动负债']
    df['金融资产'] = df['交易性金融资产'] + df['可供出售金融资产']

    df['货币资金/有息负债'] = df['货币资金'] / df['有息负债']
    df['货币资金/短期负债'] = df['货币资金'] / df['短期负债']
    df['有息负债/资产总计'] = df['有息负债'] / df['资产总计']
    df['货币资金+金融资产'] = df['货币资金'] + df['金融资产']

    score = []
    reason = []
    for index, row in df.iterrows():
        period = row['period']

        if np.isinf(row['货币资金/有息负债']) or row['货币资金/有息负债'] >= 3.0:
            score.append(100)
        else:
            if row['货币资金/有息负债'] < 2.0:
                score.append(0)
            elif row['货币资金/有息负债'] < 3.0:
                score.append(60)
            reason.append('%s : 货币资金/有息负债 = %s' % (period.year, format_pct(row['货币资金/有息负债'])))

        if row['货币资金/短期负债'] < 1.0:
            score.append(0)
            reason.append('%s : 货币资金/短期负债 = %s, 小于1' % (period.year, format_pct(row['货币资金/短期负债'])))
        else:
            score.append(100)

        if row['有息负债/资产总计'] > 0.6:
            score.append(0)
            reason.append('%s 有息负债/资产总计 = %s, 大于 60%%' % (period.year, format_pct(row['有息负债/资产总计'])))
        else:
            score.append(100)

        if row['货币资金+金融资产'] < row['有息负债']:
            score.append(0)
            reason.append('%s : 货币资金+金融资产 = %s 小于 有息负债 %s' %
                          (period.year, format_w(row['货币资金+金融资产']), format_w(row['有息负债'])))
        else:
            score.append(100)

    if len(score) > 0:
        return AnalysisResult(securities, int(float(sum(score)) / float(len(score))), reason)
    else:
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '无数据')


# ----------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------- 应收预付分析 ----------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

def analyzer_check_receivable_and_prepaid(securities: str, data_hub: DataHubEntry,
                                          database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:

    if check_industry_in(securities, ['银行', '保险', '房地产', '全国地产', '区域地产'], data_hub, database, context):
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '不适用于此行业')

    fields_balance_sheet = ['应收账款', '应收票据', '其他应收款', '长期应收款', '应收款项', '预付款项']
    fields_income_statement = ['营业收入', '营业总收入', '减:营业成本']

    df, result = batch_query_readable_annual_report_pattern(
        data_hub, securities, (years_ago(5), now()), fields_balance_sheet, fields_income_statement)
    if result is not None:
        return result

    df['应收款'] = df['应收账款'] + df['应收票据']
    df['其他应收款/营业收入'] = df['其他应收款'] / df['营业收入']
    df['应收款/营业收入'] = df['应收款'] / df['营业收入']
    df['应收款总比例'] = df['应收款/营业收入'] + df['其他应收款/营业收入']
    df['预付款项/营业收入'] = df['预付款项'] / df['营业收入']
    df['预付款项/营业成本'] = df['预付款项'] / df['减:营业成本']

    df['营业收入同比增长'] = df['营业收入'].pct_change()
    df['营业成本同比增长'] = df['减:营业成本'].pct_change()

    df['应收款同比增长'] = df['应收款'].pct_change()
    df['应收增长/营业收入增长'] = df['应收款同比增长'] / df['营业收入同比增长']

    df['预付款项同比增长'] = df['预付款项'].pct_change()
    df['预付增长/营业成本增长'] = df['预付款项同比增长'] / df['营业成本同比增长']

    score = []
    reason = []
    previous = None
    for index, row in df.iterrows():
        period = row['period']

        # ----------------------------------------------------------------------------

        if row['应收款/营业收入'] > 0.6:
            score.append(0)
            reason.append('%s : 应收款/营业收入 = %s 大于 60%%' %
                          (period.year, format_pct(row['应收款/营业收入'])))
        else:
            score.append(100)

        if row['其他应收款/营业收入'] > 0.1:
            reason.append('%s : 其他应收款/营业收入 = %s 大于 10%%' %
                          (period.year, format_pct(row['其他应收款/营业收入'])))
            score.append(0)
        else:
            score.append(100)

        # ----------------------------------------------------------------------------

        if row['应收款同比增长'] >= 10.0:
            score.append(0)
            reason.append('%s : 应收款同比大幅上升 %s (%s -> %s)' %
                          (period.year, format_pct(row['应收款同比增长']),
                           format_w(previous['应收款']), format_w(row['应收款'])))
        elif row['应收款同比增长'] <= -0.9:
            score.append(0)
            reason.append('%s : 应收款同比大幅下降 %s (%s -> %s)' %
                          (period.year, format_pct(row['应收款同比增长']),
                           format_w(previous['应收款']), format_w(row['应收款'])))
        else:
            score.append(100)

        if row['应收款/营业收入'] > 0.1 and row['应收增长/营业收入增长'] > 2.0:
            score.append(0)
            reason.append('%s : 应收增长（%s）大于 营业收入增长（%s）两倍以上' %
                          (period.year, format_pct(row['应收款同比增长']), format_pct(row['营业收入同比增长'])))

        # ----------------------------------------------------------------------------

        if row['预付款项/营业成本'] > 0.1:
            score.append(0)
            reason.append('%s : 预付款项/营业成本 = %s 大于 10%%' %
                          (period.year, format_pct(row['预付款项/营业成本'])))
        else:
            score.append(100)

        if row['预付款项/营业成本'] > 0.05:
            if row['预付增长/营业成本增长'] > 1.5:
                score.append(0)
                reason.append('%s : 预付款项增长(%s)大于营业成本增长(%s)1.5倍以上' %
                              (period.year, format_pct(row['预付款项同比增长']), format_pct(row['营业成本同比增长'])))
        else:
            score.append(100)
        previous = row

    if len(score) > 0:
        return AnalysisResult(securities, int(float(sum(score)) / float(len(score))), reason)
    else:
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '无数据')


# ----------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------- 资产构成分析 ----------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

def analyzer_asset_composition(securities: str, data_hub: DataHubEntry,
                               database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:

    nop(database, context)

    fields_balance_sheet = ['商誉', '在建工程', '固定资产', '资产总计', '负债合计']
    # fields_income_statement = ['息税前利润']

    df, result = batch_query_readable_annual_report_pattern(
        data_hub, securities, (years_ago(5), now()), fields_balance_sheet)
    if result is not None:
        return result

    df['净资产'] = df['资产总计'] - df['负债合计']
    df['商誉/净资产'] = df['商誉'] / df['净资产']
    df['商誉/总资产'] = df['商誉'] / df['资产总计']
    df['在建工程/总资产'] = df['在建工程'] / df['资产总计']
    df['固定资产/总资产'] = df['固定资产'] / df['资产总计']
    # df['税前利润/固定资产'] = df['息税前利润'] / df['固定资产']

    score = []
    reason = []
    for index, row in df.iterrows():
        period = row['period']

        # ----------------------------------------------------------------------------

        if row['净资产'] < 10000.0:
            score.append(0)
            reason.append('%s : 净资产（%s）为负或过低（资不抵债）' % (period.year, row['净资产']))

        if row['商誉/净资产'] > 0.2 or row['商誉/总资产'] > 0.1:
            score.append(0)
            reason.append('%s : 商誉/净资产 = %s，商誉/总资产 = %s - 占比过高' %
                          (period.year, format_pct(row['商誉/净资产']), format_pct(row['商誉/总资产'])))

        if row['在建工程/总资产'] > 0.1:
            score.append(0)
            reason.append('%s : 在建工程/总资产 = %s - 占比过高' % (period.year, format_pct(row['在建工程/总资产'])))

        judgement = ''
        if row['固定资产/总资产'] < 0.1:
            score.append(100)
        elif row['固定资产/总资产'] < 0.3:
            score.append(90)
        elif row['固定资产/总资产'] < 0.4:
            score.append(80)
            judgement = '中资产公司'
        elif row['固定资产/总资产'] < 0.6:
            score.append(70)
            judgement = '中资产公司'
        else:
            score.append(60)
            judgement = '重资产公司'
        if judgement != '':
            reason.append('%s : 固定资产/总资产 = %s - %s' % (period.year, format_pct(row['固定资产/总资产']), judgement))

        # if row['税前利润/固定资产'] < 0.08:
        #     score.append(50)
        #     reason.append('%s : 税前利润/固定资产 = %s - 小于平均社会平均资本回报率' %
        #                   (period.year, format_pct(row['税前利润/固定资产'])))

    if len(reason) == 0:
        reason.append('正常')

    if len(score) > 0:
        return AnalysisResult(securities, int(float(sum(score)) / float(len(score))), reason)
    else:
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '无数据')


def analyzer_income_statement(securities: str, data_hub: DataHubEntry,
                              database: DatabaseEntry, context: AnalysisContext) -> AnalysisResult:

    if check_industry_in(securities, ['银行', '保险', '房地产', '全国地产', '区域地产'], data_hub, database, context):
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '不适用于此行业')

    fields_balance_sheet = ['商誉', '在建工程', '固定资产', '资产总计', '负债合计']
    fields_income_statement = ['营业利润', '营业收入', '营业总收入', '净利润(含少数股东损益)',
                               '加:营业外收入', '减:资产减值损失', '减:营业成本',
                               '减:销售费用', '减:管理费用', '减:财务费用',
                               '减:资产减值损失']
    fields_cash_flow_statement = ['经营活动产生的现金流量净额']

    df, result = batch_query_readable_annual_report_pattern(
        data_hub, securities, (years_ago(5), now()),
        fields_balance_sheet, fields_income_statement, fields_cash_flow_statement)
    if result is not None:
        return result

    df['毛利润'] = df['营业收入'] - df['减:营业成本']
    df['营业利润率'] = df['营业利润'] / df['营业收入']

    df['财务费用正'] = df['减:财务费用'].apply(lambda x: x if x > 0 else 0)
    df['三费'] = df['减:销售费用'] + df['减:管理费用'] + df['财务费用正']

    df['三费/营业总收入'] = df['三费'] / df['营业总收入']
    df['三费/毛利润'] = df['三费'] / df['毛利润']

    df['营业外收入/营业总收入'] = df['加:营业外收入'] / df['营业总收入']
    df['资产减值损失/营业总收入'] = df['减:资产减值损失'] / df['营业总收入']
    df['经营现金流/净利润'] = df['经营活动产生的现金流量净额'] / df['净利润(含少数股东损益)']

    df['销售费用/营业收入'] = df['减:销售费用'] / df['营业收入']
    df['管理费用/营业收入'] = df['减:管理费用'] / df['营业收入']

    df['三费/营业总收入同比'] = df['三费/营业总收入'].pct_change()
    df['销售费用/营业收入同比'] = df['销售费用/营业收入'].pct_change()
    df['管理费用/营业收入同比'] = df['管理费用/营业收入'].pct_change()

    score = []
    reason = []
    previous = None
    aset_lost = 0
    for index, row in df.iterrows():
        period = row['period']

        # ----------------------------------------------------------------------------

        if row['营业总收入'] < 0.1:
            score.append(0)
            reason.append('%s : 营业总收入 %s 小于0' % (period.year, format_w(row['营业总收入'])))
            previous = row
            continue

        if row['毛利润'] < 0.1:
            score.append(0)
            reason.append('%s : 毛利润 %s 小于0' % (period.year, format_w(row['毛利润'])))
            previous = row
            continue

        # ----------------------------------------------------------------------------

        if abs(row['销售费用/营业收入同比'] > 0.4):
            score.append(0)
            reason.append('%s : 销售费用/营业收入 变化超过40%% (%s -> %s)' %
                          (period.year, format_pct(previous['销售费用/营业收入']), format_pct(row['销售费用/营业收入'])))

        if abs(row['管理费用/营业收入同比'] > 0.4):
            score.append(0)
            reason.append('%s : 管理费用/营业收入 变化超过40%% (%s -> %s)' %
                          (period.year, format_pct(previous['管理费用/营业收入']), format_pct(row['管理费用/营业收入'])))

        # ----------------------------------------------------------------------------

        if row['经营现金流/净利润'] > 1.0:
            score.append(100)
        elif row['经营现金流/净利润'] > 0.8:
            score.append(100 * row['经营现金流/净利润'])
            reason.append('%s : 经营现金流/净利润 = %s < 1.0' %
                          (period.year, format_pct(row['经营现金流/净利润'])))

        # ----------------------------------------------------------------------------

        if row['营业外收入/营业总收入'] > 0.1:
            score.append(0)
            reason.append('%s : 营业外收入占比%s，超过10%%' %
                          (period.year, format_pct(row['营业外收入/营业总收入'])))

        if abs(row['资产减值损失/营业总收入']) > 0.2:
            aset_lost += 1
            reason.append('%s : 资产减值损失/营业总收入 = %s，超过20%%' %
                          (period.year, format_pct(abs(row['资产减值损失/营业总收入']))))

        # ----------------------------------------------------------------------------

        # df['营业利润率']
        # 越大越好，并且需要同行及历史比较

        # ----------------------------------------------------------------------------

        if abs(row['三费/营业总收入']) < 0.2:
            score.append(100)
        elif abs(row['三费/营业总收入']) < 0.4:
            score.append(60)
        else:
            score.append(0)
            reason.append('%s : 三费/营业总收入 = %s，超过40%%' % (period.year, format_pct(row['三费/营业总收入'])))

        if row['三费/毛利润'] < 0.3:
            pass
        elif row['三费/毛利润'] < 0.7:
            score.append(60)
            reason.append('%s : 三费/毛利润 = %s，在30%% ~ 70%%之间，良' %
                          (period.year, format_pct(row['三费/毛利润'])))
        else:
            score.append(0)
            reason.append('%s : 三费/毛利润 = %s，大于70%%，差' %
                          (period.year, format_pct(row['三费/毛利润'])))

        # ----------------------------------------------------------------------------

        previous = row

    if aset_lost >= 2:
        score.append(0)
        reason.append('注意：有 %s 次较大资产减值损失（超过营业总收入20%%）' % aset_lost)

    if len(reason) == 0:
        reason.append('正常')

    if len(score) > 0:
        return AnalysisResult(securities, int(float(sum(score)) / float(len(score))), reason)
    else:
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '无数据')


# ----------------------------------------------------------------------------------------------------------------------

METHOD_LIST = [
    ('3ee3a4ff-a2cf-4244-8f45-c319016ee16b', '[T001] 现金流肖像',    '根据经营现金流,投资现金流,筹资现金流的情况为企业绘制画像',       analyzer_stock_portrait),
    ('7e132f82-a28e-4aa9-aaa6-81fa3692b10c', '[T002] 货币资金分析',  '分析货币资金，详见excel中的对应的ID行',                         analyzer_check_monetary_fund),
    ('7b0478d3-1e15-4bce-800c-6f89ee743600', '[T003] 应收预付分析',  '分析应收款和预付款，详见excel中的对应的ID行',                   analyzer_check_receivable_and_prepaid),
    ('fff6c3cf-a6e5-4fa2-9dce-7d0566b581a1', '[T004] 资产构成分析',  '净资产，商誉，在建工程等项目分析，详见excel中的对应的ID行',      analyzer_asset_composition),
    ('d2ced262-7a03-4428-9220-3d4a2a8fe201', '[T005] 利润表分析',    '分析利润，费用以及它们的构成，详见excel中的对应的ID行',          analyzer_income_statement),

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




