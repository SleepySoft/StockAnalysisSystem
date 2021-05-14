import pandas as pd

from StockAnalysisSystem.core.Utility.common import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.Utility.AnalyzerUtility import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.Database.DatabaseEntry import DatabaseEntry


# ------------------------------------------------------ 01 - 05 -------------------------------------------------------

def equity_interest_pledge_too_high(securities: str, time_serial: tuple, data_hub: DataHubEntry,
                                    database: DatabaseEntry, context: AnalysisContext, **kwargs) -> AnalysisResult:
    nop(database, context, kwargs)

    query_fields = ['质押次数', '无限售股质押数量', '限售股份质押数量', '总股本', '质押比例']
    if not data_hub.get_data_center().check_readable_name(query_fields):
        return AnalysisResult(securities, None, AnalysisResult.SCORE_NOT_APPLIED, '无法识别的字段名', '无法识别的字段名')

    df = data_hub.get_data_center().query('Stockholder.PledgeStatus', securities, (years_ago(2), now()),
                                          fields=query_fields + ['stock_identity', 'due_date'], readable=True)
    if df is None or len(df) == 0:
        return AnalysisResult(securities, None, AnalysisResult.SCORE_NOT_APPLIED, '没有数据', '没有数据')
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
                reason.append('%s: 质押比例：%.2f%%' % (str(due_date.date()), pledge_rate))
            previous_pledge_times = pledge_times

    if len(reason) == 0:
        brief = '近4年没有超过20%%的质押记录'
        reason = brief
    else:
        brief = '近4年有%s次超过20%%的质押记录' % len(reason)
        reason = brief

    return AnalysisResult(securities, None, score, reason, brief)


def analysis_dispersed_ownership(securities: str, time_serial: tuple, data_hub: DataHubEntry,
                                 database: DatabaseEntry, context: AnalysisContext, **kwargs) -> AnalysisResult:
    nop(database, context, kwargs)
    df = data_hub.get_data_center().query('Stockholder.Statistics', securities, (years_ago(3), now()))
    if df is None or len(df) == 0:
        return AnalysisResult(securities, None, AnalysisResult.SCORE_NOT_APPLIED, '没有数据', '没有数据')
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
            return AnalysisResult(securities, None, AnalysisResult.SCORE_NOT_APPLIED,
                                  '缺少必要数据，请确保数据包含tushare pro数据源', '没有数据')
        if largest_ratio < 0.1:
            score = 0
            reason.append('%s: 最大股东 %s 持股比例为%.2f%%，小于10%%' %
                          (period.year, biggest_holder, largest_ratio * 100))
        else:
            reason.append('%s: 最大股东 %s 持股比例为%.2f%%' %
                          (period.year, biggest_holder, largest_ratio * 100))

    if len(reason) == 0:
        reason.append('没有数据')
    brief = '正常' if score != 0 else '最大股东持股比例 < 10%%'

    return AnalysisResult(securities, None, score, reason) if applied else \
        AnalysisResult(securities, None, AnalysisResult.SCORE_NOT_APPLIED, reason, brief)


def analysis_stock_unlock(securities: str, time_serial: tuple, data_hub: DataHubEntry,
                          database: DatabaseEntry, context: AnalysisContext, **kwargs) -> AnalysisResult:
    nop(time_serial, database, context, kwargs)
    no_data_result = AnalysisResult(securities, None, AnalysisResult.SCORE_PASS, '前三个月或后半年内没有解禁数据', '无解禁数据')

    df: pd.DataFrame = data_hub.get_data_center().query('Stockholder.StockUnlock', securities, (years_ago(2), now()))
    if df is None or df.empty:
        return no_data_result

    df = df[df['float_date'].notna()]
    df['float_date'] = df['float_date'].apply(text_auto_time)
    mask = (df['float_date'] > days_ago(90)) & (df['float_date'] <= days_after(180))
    df = df.loc[mask]
    if df is None or df.empty:
        return no_data_result

    df_group = df.groupby('float_date')

    reasons = []
    float_share_sum = 0
    for g, df in df_group:
        float_date = g
        float_share = sum(df['float_share'])
        float_ratio = sum(df['float_ratio'])

        float_share_sum += float_share
        reasons.append('%s: 解禁%s股，占总股份%s%%' % (float_date.date(), float_share, float_ratio))

    # for index, row in df.iterrows():
    #     float_date = row['float_date']
    #     float_share = row['float_share']
    #     float_ratio = row['float_ratio']
    #
    #     # Maybe have not converted to datetime but keeping str
    #     # Maybe there're a lot of unlock in one day
    #
    #     if not isinstance(float_date, datetime.datetime):
    #         float_date = text_auto_time(float_date)
    #     if days_ago(90) < float_date < days_after(180):
    #         reasons.append('%s: 解禁%s股，占总股份%s%%' % (float_date.date(), float_share, float_ratio))

    brief = '共解禁%s股' % float_share_sum
    return AnalysisResult(securities, None, AnalysisResult.SCORE_FAIL, reasons, brief) if len(reasons) > 0 else \
        AnalysisResult(securities, None, AnalysisResult.SCORE_PASS, '前三个月或后半年内没有解禁数据', '无解禁数据')


def analysis_repurchase(securities: str, time_serial: tuple, data_hub: DataHubEntry,
                        database: DatabaseEntry, context: AnalysisContext, **kwargs) -> AnalysisResult:
    nop(time_serial, database, context, kwargs)
    df = data_hub.get_data_center().query('Stockholder.Repurchase', securities, (years_ago(1), now()))
    if df is None or len(df) == 0:
        return AnalysisResult(securities, None, AnalysisResult.SCORE_FAIL, '前后一年内没有回购数据', '无回购数据')
    # df = df.where(df.notnull(), None)

    volume = 0
    reasons = []
    for index, row in df.iterrows():
        proc = row['proc']

        if proc != '股东大会通过':
            # For multiple calculate, just count pass
            continue

        ann_date = row['ann_date']

        # TS_ISSUE: Some fields may miss
        end_date = row['end_date'] if 'end_date' in df.columns else None

        volume = row['vol'] if 'vol' in df.columns else None
        low_limit = row['low_limit'] if 'low_limit' in df.columns else None
        high_limit = row['high_limit'] if 'high_limit' in df.columns else None

        end_date_text = ('截止%s' % end_date.date()) if \
            isinstance(end_date, datetime.datetime) and end_date is not pd.NaT else ''

        if not pd.isnull(low_limit) and not pd.isnull(high_limit):
            if low_limit == high_limit:
                price_text = '将以%s元的价格' % low_limit
            else:
                price_text = '将以%s - %s元的价格' % (low_limit, high_limit)
        elif not pd.isnull(low_limit):
            price_text = '将以最低%s元的价格' % low_limit
        elif not pd.isnull(high_limit):
            price_text = '将以最高%s元的价格' % high_limit
        else:
            price_text = ''

        volume += int(volume)
        volume_text = ('%s股' % volume) if not pd.isnull(volume) else ''

        reasons.append('%s: 股东大会通过，%s%s回购%s股票' %
                       (ann_date.date(), end_date_text, price_text, volume_text))

    brief = '期间计划回购%s股' % volume
    return AnalysisResult(securities, None, AnalysisResult.SCORE_PASS, reasons, brief) if len(reasons) > 0 else \
        AnalysisResult(securities, None, AnalysisResult.SCORE_FAIL, '前后一年内没有回购数据', '近一年无数据')


def analysis_increase_decrease(securities: str, time_serial: tuple, data_hub: DataHubEntry,
                               database: DatabaseEntry, context: AnalysisContext, **kwargs) -> AnalysisResult:
    nop(time_serial, database, context, kwargs)
    no_data_result = AnalysisResult(securities, None, AnalysisResult.SCORE_NOT_APPLIED, '前后一年内没有增减持数据', '近一年无数据')

    df = data_hub.get_data_center().query('Stockholder.ReductionIncrease', securities, (years_ago(2), now()))
    if df is None or len(df) == 0:
        return no_data_result

    volume = 0
    reasons = []
    for index, row in df.iterrows():
        stock_holder = row['stock_holder']
        holder_type = row['holder_type']
        holder_type = {
            'G': '高管',
            'P': '个人',
            'C': '公司',
        }.get(holder_type, '')

        increase_or_decrease = row['in_de']
        change_vol = row['change_vol'] if 'change_vol' in df.columns else '?'
        change_ratio = row['change_ratio'] if 'change_ratio' in df.columns else '?'
        avg_price = row['avg_price'] if 'avg_price' in df.columns else '?'

        begin_date = text_auto_time(row['begin_date'])
        close_date = text_auto_time(row['close_date'])

        if (begin_date is not None and days_ago(365) < begin_date < days_after(365)) or \
           (close_date is not None and days_ago(365) < close_date < days_after(365)):
            if increase_or_decrease == 'IN':
                volume += change_vol
                operation = '增持'
            elif increase_or_decrease == 'DE':
                volume -= change_vol
                operation = '减持'
            else:
                operation = ''

            if operation != '':
                reasons.append('%s - %s: %s[%s]以平均价格%s元%s%s股，占流通股%s%%' %
                               (begin_date.date() if begin_date is not None else '?',
                                close_date.date() if close_date is not None else '?',
                                holder_type, stock_holder, avg_price, operation, change_vol, change_ratio))

    if len(reasons) == 0:
        return no_data_result

    if volume > 0:
        conclusion = '此期间净增持%s股' % volume
    elif volume < 0:
        conclusion = '此期间净减持%s股' % -volume
    else:
        conclusion = '此期间增持减持持平'
    reasons.append(conclusion)
    final_score = AnalysisResult.SCORE_FAIL if volume < 0 else AnalysisResult.SCORE_PASS

    return AnalysisResult(securities, None, final_score, reasons, conclusion.replace('此', ''))


# ------------------------------------------------------ 05 - 10 -------------------------------------------------------


# ------------------------------------------------------ 11 - 15 -------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------

METHOD_LIST = [
    # 1 - 5
    ('4ccedeea-b731-4b97-9681-d804838e351b', '股权质押过高',      '排除股权质押高于50%的公司',              equity_interest_pledge_too_high),
    ('e515bd4b-db4f-49e2-ac55-1927a28d2a1c', '股权分散',          '排除最大股东持股不足10%的企业',          analysis_dispersed_ownership),
    ('41e20665-4b1b-4423-97de-33764de09e02', '非流通股解禁',      '排除最近有非流通股解禁的企业',           analysis_stock_unlock),
    ('1dfe5faa-183c-4b30-aa5f-e0c55e064c31', '股份回购',          '选择最近有回购的企业',                   analysis_repurchase),
    ('b646a253-33ec-4313-a5f3-7419363079a8', '股东增减持',        '排除最近有减持的企业，选择有增持的企业', analysis_increase_decrease),
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

def analysis(methods: [str], securities: [str], time_serial: tuple,
             data_hub: DataHubEntry, database: DatabaseEntry, **kwargs) -> [AnalysisResult]:
    return standard_dispatch_analysis(methods, securities, time_serial, data_hub, database, kwargs, METHOD_LIST)


















