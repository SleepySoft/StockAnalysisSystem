import pandas as pd

from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.digit_utility import *
from StockAnalysisSystem.core.Utiltity.AnalyzerUtility import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.Database.DatabaseEntry import DatabaseEntry


# ------------------------------------------------------ 01 - 05 -------------------------------------------------------

def analysis_finance_report_sign(securities: str, time_serial: tuple, data_hub: DataHubEntry,
                                 database: DatabaseEntry, context: AnalysisContext, **kwargs) -> [AnalysisResult]:
    nop(database, kwargs)
    if context.cache.get('finance_audit', None) is None:
        context.cache['finance_audit'] = data_hub.get_data_center().query('Finance.Audit', None, time_serial)
    df = context.cache.get('finance_audit', None)

    error_report = check_gen_report_when_data_missing(df, securities, 'Finance.Audit',
                                                      ['stock_identity', 'period', 'conclusion'])
    if error_report is not None:
        return error_report

    df_slice = df[df['stock_identity'] == securities]
    # df_slice_in_4_years = df_slice[df_slice['period'] > years_ago(5)]

    results = []
    for index, row in df_slice.iterrows():
        reason = []
        period = row['period']
        conclusion = row['conclusion']

        if pd.isnull(conclusion):
            score = AnalysisResult.SCORE_NOT_APPLIED
            reason.append(date2text(period) + ' : No sign data.')
        elif conclusion != '标准无保留意见':
            score = AnalysisResult.SCORE_FAIL
            reason.append(date2text(period) + ' : ' + conclusion)
        else:
            score = AnalysisResult.SCORE_PASS
        results.append(AnalysisResult(securities, period, score, reason, AnalysisResult.WEIGHT_ONE_VOTE_VETO))

    return results

    # if len(reason) == 0:
    #     reason.append('近四年均为标准无保留意见')

    # return AnalysisResult(securities, score, reason, AnalysisResult.WEIGHT_ONE_VOTE_VETO)


def analysis_consecutive_losses(securities: str, time_serial: tuple, data_hub: DataHubEntry,
                                database: DatabaseEntry, context: AnalysisContext, **kwargs) -> [AnalysisResult]:
    nop(database, context, kwargs)
    df, result = query_readable_annual_report_pattern(data_hub, 'Finance.IncomeStatement',
                                                      securities, time_serial,
                                                      ['利润总额', '营业利润'])
    if result is not None:
        return result

    results = []
    for index, row in df.iterrows():
        score = 100
        reason = []
        period = row['period']

        if row['利润总额'] < 0:
            score -= 50
            reason.append(date2text(period) + '：利润总额 ' + format_w(row['利润总额']))
        if row['营业利润'] < 0:
            score -= 50
            reason.append(date2text(period) + '：营业利润 ' + format_w(row['营业利润']))
        results.append(AnalysisResult(securities, period, score, reason))

    return results

    # if len(reason) == 0:
    #     reason.append('近四年不存在亏损')
    #
    # return AnalysisResult(securities, score, reason)


def analysis_profit_structure(securities: str, time_serial: tuple, data_hub: DataHubEntry,
                              database: DatabaseEntry, context: AnalysisContext, **kwargs) -> [AnalysisResult]:
    nop(database, context, kwargs)
    df, result = query_readable_annual_report_pattern(data_hub, 'Finance.IncomeStatement',
                                                      securities, time_serial,
                                                      ['营业收入', '营业总收入', '其他业务收入'])
    if result is not None:
        return result

    results = []
    for index, row in df.iterrows():
        score = 100
        reason = []
        period = row['period']

        if row['营业收入'] < 0.001:
            reason.append(str(period) + ': 营业收入为0，可能数据缺失')
            results.append(AnalysisResult(securities, period, AnalysisResult.SCORE_NOT_APPLIED, reason))
        else:
            other_operating_profit = row['其他业务收入'] / row['营业收入']
            # main_operating_profit = row['营业收入'] - row['其他业务收入']
            # main_operating_profit_ratio = main_operating_profit / row['营业收入']

            if other_operating_profit > 0.3:
                score = 0
                reason.append('%s: 其他业务收入：%s万；营业总收入：%s万；其它业务收入占比：%.2f%%' %
                              (period, row['其他业务收入'] / 10000, row['营业收入'] / 10000, other_operating_profit * 100))
            results.append(AnalysisResult(securities, period, score, reason))
    return results

    # return AnalysisResult(securities, score, reason) if applied else \
    #     AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, reason)


def analysis_cash_loan_both_high(securities: str, time_serial: tuple, data_hub: DataHubEntry,
                                 database: DatabaseEntry, context: AnalysisContext, **kwargs) -> [AnalysisResult]:
    nop(database, context, kwargs)
    fields_balance_sheet = ['短期借款', '长期借款', '货币资金', '其他流动资产',  '应付债券',
                            '一年内到期的非流动负债', '应收票据', '其他流动负债', '流动负债合计',
                            '资产总计']
    fields_income_statement = ['净利润(含少数股东损益)', '减:财务费用']

    df_balance_sheet, result = query_readable_annual_report_pattern(
        data_hub, 'Finance.BalanceSheet', securities, time_serial, fields_balance_sheet)
    if result is not None:
        return result

    df_income_statement, result = query_readable_annual_report_pattern(
        data_hub, 'Finance.IncomeStatement', securities, time_serial, fields_income_statement)
    if result is not None:
        return result

    df = pd.merge(df_balance_sheet, df_income_statement, how='left', on=['stock_identity', 'period'])

    results = []
    for index, row in df.iterrows():
        score = 100
        reason = []
        period = row['period']

        cash = row['货币资金'] + row['其他流动资产']
        loan = row['短期借款'] + row['长期借款'] + row['一年内到期的非流动负债'] + row['应付债券'] + row['其他流动负债']

        if row['资产总计'] < 1.0:
            reason.append(str(period) + ': 资产总计为0，可能数据缺失')
            results.append(AnalysisResult(securities, period, AnalysisResult.SCORE_NOT_APPLIED, reason))
            continue

        if row['净利润(含少数股东损益)'] < 1.0:
            reason.append(str(period) + ': 净利润(含少数股东损益) = %.2f，不适用' % row['净利润(含少数股东损益)'])
            results.append(AnalysisResult(securities, period, AnalysisResult.SCORE_NOT_APPLIED, reason))
            continue

        if loan < 0.001:
            reason.append(str(period) + ': 流动负债合计为0，可能数据缺失')
            results.append(AnalysisResult(securities, period, AnalysisResult.SCORE_NOT_APPLIED, reason))
            continue

        loan_vs_totol_asset = loan / row['资产总计']
        fin_fee_vs_benefit = row['减:财务费用'] / row['净利润(含少数股东损益)']

        # 货币资金+其他流动资产 > 短期借款+长期借款+一年到期的非流动负债+应付债券
        # 贷款占资产总额的比例大于50%
        # 利息费用与净利润比例大于30%（康美并不符合），排除
        if 1.0 < cash / loan < 1.7 and loan_vs_totol_asset > 0.3:
            score = 0
            reason.append('%s: 资金：%s万；借款：%s万。贷款总资产比：%.2f%%。利息净利润比%.2f%%' %
                          (period, cash / 10000, loan / 10000, loan_vs_totol_asset * 100, fin_fee_vs_benefit * 100))
        results.append(AnalysisResult(securities, period, score, reason))
    return results

    # if len(reason) == 0:
    #     reason.append('正常')
    # return AnalysisResult(securities, score, reason) if applied else \
    #     AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, reason)


def goodwill_is_too_high(securities: str, time_serial: tuple, data_hub: DataHubEntry,
                         database: DatabaseEntry, context: AnalysisContext, **kwargs) -> [AnalysisResult]:
    nop(database, context, kwargs)
    df, result = query_readable_annual_report_pattern(data_hub, 'Finance.BalanceSheet',
                                                      securities, time_serial,
                                                      ['商誉', '资产总计', '负债合计'])
    if result is not None:
        return result

    results = []
    for index, row in df.iterrows():
        score = 100
        reason = []
        period = row['period']

        net_assets = row['资产总计'] - row['负债合计']

        if row['资产总计'] < 0.001 or net_assets < 0.001:
            reason.append('资产为0，可能数据不全')
            results.append(AnalysisResult(securities, period, AnalysisResult.SCORE_NOT_APPLIED, reason))
            continue

        goodwill_vs_net_assets = row['商誉'] / net_assets
        goodwill_vs_total_assets = row['商誉'] / row['资产总计']

        if goodwill_vs_net_assets >= 0.2 or goodwill_vs_total_assets >= 0.1:
            score = 0
            reason.append('%s: 商誉/净资产 = %.2f%% ; 商誉/资产总计 = %.2f%%' %
                          (str(period), goodwill_vs_net_assets * 100, goodwill_vs_total_assets * 100))
        results.append(AnalysisResult(securities, period, score, reason))
    return results

    # if len(reason) == 0:
    #     reason.append('正常')
    # return AnalysisResult(securities, score, reason) if applied else \
    #     AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, reason)


def interest_too_high(securities: str, time_serial: tuple, data_hub: DataHubEntry,
                      database: DatabaseEntry, context: AnalysisContext, **kwargs) -> [AnalysisResult]:
    nop(database, context, kwargs)
    df, result = query_readable_annual_report_pattern(data_hub, 'Finance.BalanceSheet',
                                                      securities, time_serial,
                                                      ['减:利息支出', '净利润(不含少数股东损益)'])
    if result is not None:
        return result

    results = []
    for index, row in df.iterrows():
        score = 100
        reason = []
        period = row['period']

        if row['净利润(不含少数股东损益)'] <= 0:
            if row['减:利息支出'] > 10000:
                score = 0
                reason.append('%s: 母公司净利润小于等于0，而存在利息支出 = %.2f%%' %
                              (str(period), row['减:利息支出']))
            else:
                score = min(score, 50)
                reason.append('%s: 母公司净利润小于等于0' % str(period))
            results.append(AnalysisResult(securities, period, score, reason))
            continue

        interest_income_ratio = row['减:利息支出'] / row['净利润(不含少数股东损益)']
        if interest_income_ratio >= 0.3:
            score = 0
            reason.append('%s: 利息支出占母公司净利润比例 = %.2f%%' %
                          (str(period), interest_income_ratio))
        elif interest_income_ratio >= 0.1:
            score = min(score, 50)
            reason.append('%s: 利息支出占母公司净利润比例 = %.2f%%' %
                          (str(period), interest_income_ratio))
        results.append(AnalysisResult(securities, period, score, reason))
    return results

    # if len(reason) == 0:
    #     reason.append('正常')
    # return AnalysisResult(securities, score, reason) if applied else \
    #     AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '')


# ------------------------------------------------------ 06 - 10 -------------------------------------------------------

def analysis_current_and_quick_ratio(securities: str, time_serial: tuple, data_hub: DataHubEntry,
                                     database: DatabaseEntry, context: AnalysisContext, **kwargs) -> [AnalysisResult]:
    nop(database, context, kwargs)

    df = data_hub.get_data_center().query_from_factor(
        'Factor.Finance', securities, time_serial, fields=['流动比率', '速动比率'], readable=True)
    if df is None or len(df) == 0:
        return AnalysisResult(securities, None, AnalysisResult.SCORE_NOT_APPLIED, '')

    # Annual report
    df = df[df['period'].dt.month == 12]

    results = []
    for index, row in df.iterrows():
        score = 100
        reason = []
        period = row['period']

        if row['流动比率'] < 2.0:
            score -= 50
            reason.append('%s: 流动比率为%.2f < 2.0' % (str(period), row['流动比率']))
        else:
            reason.append('%s: 流动比率为%.2f - 合格' % (str(period), row['流动比率']))

        if row['速动比率'] < 1.0:
            score -= 50
            reason.append('%s: 速动比率为%.2f < 1.0' % (str(period), row['速动比率']))
        else:
            reason.append('%s: 速动比率为%.2f - 合格' % (str(period), row['速动比率']))

        results.append(AnalysisResult(securities, period,  score, reason))
    return results

    # if total > 0 and len(reason) == 0:
    #     reason.append('正常 - 平均流动比率为%.2f，平均速动比率为%.2f' % (df['流动比率'].mean(), df['速动比率'].mean()))
    # return AnalysisResult(securities, score / total, reason) if total > 0 else \
    #     AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '')


def analysis_roe_roa(securities: str, time_serial: tuple, data_hub: DataHubEntry,
                     database: DatabaseEntry, context: AnalysisContext, **kwargs) -> [AnalysisResult]:
    nop(database, context, kwargs)

    df = data_hub.get_data_center().query_from_factor(
        'Factor.Finance', securities, time_serial, fields=['总资产收益率', '净资产收益率'], readable=True)
    if df is None or len(df) == 0:
        return AnalysisResult(securities, None, AnalysisResult.SCORE_NOT_APPLIED, '')

    # Annual report
    df = df[df['period'].dt.month == 12]

    results = []
    for index, row in df.iterrows():
        score = 100
        reason = []
        period = row['period']

        if row['总资产收益率'] < 0.05:
            score -= 50
            reason.append('%s: 总资产收益率为%s%% - 过低' %
                          (str(period), format_pct(row['总资产收益率'])))
        elif row['总资产收益率'] > 0.15:
            score -= 50
            reason.append('%s: 总资产收益率为%s%% - 偏高，需要引起注意' %
                          (str(period), format_pct(row['总资产收益率'])))
        else:
            # Theory: 7.5% - 13%, but we use 5% - 15% for wider tolerance.
            reason.append('%s: 总资产收益率为%s%% - 合理' %
                          (str(period), format_pct(row['总资产收益率'])))
            pass

        if row['净资产收益率'] < 0.15:
            score -= 50
            reason.append('%s: 净资产收益率为%s%% - 偏低' %
                          (str(period), format_pct(row['净资产收益率'])))
        elif row['净资产收益率'] > 0.40:
            score = 0
            reason.append('%s: 净资产收益率为%s%% - 过高，可能是造假或偶然因素' %
                          (str(period), format_pct(row['净资产收益率'])))
        else:
            # Theory: 15% - 39%.
            reason.append('%s: 净资产收益率为%s%% - 合理' %
                          (str(period), format_pct(row['净资产收益率'])))

        results.append(AnalysisResult(securities, period, score, reason))
    return results

    # if total > 0 and len(reason) == 0:
    #     reason.append('正常 - 平均总资产收益率为%.2f，平均净资产收益率为%.2f' %
    #                   (df['总资产收益率'].mean(), df['净资产收益率'].mean()))
    # return AnalysisResult(securities, score / total, reason) if total > 0 else \
    #     AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, '')


# ------------------------------------------------------ 11 - 15 -------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------

METHOD_LIST = [
    # 1 - 5
    ('3b01999c-3837-11ea-b851-27d2aa2d4e7d', '财报非标',        '排除财报非标的公司',                   analysis_finance_report_sign),
    ('b0e34011-c5bf-4ac3-b6a4-c15e5ea150a6', '连续亏损',        '排除营业利润或利润总额连续亏损的公司', analysis_consecutive_losses),
    # oth_b_income field missing for lots of securities. This analyzer may not work.
    ('d811ebd6-ee28-4d2f-b7e0-79ce0ecde7f7', '非主营业务过高',  '排除主营业务占比过低的公司',           analysis_profit_structure),
    ('2c05bb4c-935e-4be7-9c04-ae12720cd757', '存贷双高',        '排除存贷双高的公司',                   analysis_cash_loan_both_high),
    # ('e6ab71a9-0c9f-4500-b2db-d682af567f70', '商誉过高',        '排除商誉过高的公司',                  goodwill_is_too_high),

    # These data in tushare always 0
    # ('a442023d-81e9-47c7-aeb6-7de478cdbc1b', '利息吞噬利润',    '排除利息占比净利润过高的公司',        interest_too_high),
    
    ('a460a24e-2261-4ed1-8c42-84025e495bed', '流动速动',        '排除流动比率和速动比率不达标的公司',    analysis_current_and_quick_ratio),
    ('fb82909b-c7a3-427a-8bea-880c48c25027', '资产收益',        '分析资产收益率及净资产收益率',          analysis_roe_roa),
]


def plugin_prob() -> dict:
    return {
        'plugin_id': '7b59e0e4-5572-4cd8-8982-baa94f8af3d9',
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

def analysis(methods: [str], securities: [str], time_serial: tuple,
             data_hub: DataHubEntry, database: DatabaseEntry, **kwargs) -> [AnalysisResult]:
    return standard_dispatch_analysis(methods, securities, time_serial, data_hub, database, kwargs, METHOD_LIST)


















