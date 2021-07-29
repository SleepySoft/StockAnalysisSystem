import os

import pandas as pd
import tushare as ts
from StockAnalysisSystem.core.config import Config
from StockAnalysisSystem.core.Utility.CollectorUtility import *


root_path = os.path.dirname(os.path.dirname(__file__))
config = Config()
config.load_config(os.path.join(root_path, 'config.json'))
token = config.get('TS_TOKEN')
pro = ts.pro_api(token)


# result = pro.daily_basic(ts_code='', trade_date='20200805')
# print(result)

# result = pro.daily_basic(ts_code='600000.SH', start_date='19900101', end_date='20210720')
# print(len(result))          # 4500, Reach end_date, not fits start_date
# print('%s - %s' % (min(result['trade_date']), max(result['trade_date'])))
# print(result)

# result = pro.index_daily(ts_code='000001.SH', start_date='19000101', end_date='20150101')
# print(len(result))          # 4500, Reach end_date, not fits start_date
# print('%s - %s' % (min(result['trade_date']), max(result['trade_date'])))
# print(result)

# # Not support
# result = pro.index_daily(ts_code='', trade_date='20200805')
# print(result)


# result = pro.trade_cal(exchange='', start_date='19900101', end_date='20210726')
# print(len(result))
# print('%s - %s' % (min(result['cal_date']), max(result['cal_date'])))
# print(result)


# result = pro.repurchase(ts_code='000333.SZ', start_date='19900101', end_date='20210726')
# print(len(result))
# print('%s - %s' % (min(result['ann_date']), max(result['ann_date'])))
# print(result)


# result = pro.repurchase(ann_date='20181010')
# print(result)


# result = pro.share_float(ts_code='603301.SH', start_date='20180402', end_date='20180411')
# print(len(result))
# print('%s - %s' % (min(result['ann_date']), max(result['ann_date'])))
# print(result)


# result = pro.pledge_stat(ts_code='000014.SZ')
# print('%s - %s' % (min(result['end_date']), max(result['end_date'])))
# print(result)
#
# result = pro.pledge_stat(ts_code='000014.SZ', end_date='20180928')
# print('%s - %s' % (min(result['end_date']), max(result['end_date'])))
# print(result)

# result = pro.pledge_stat(end_date='20191227')
# print(result)           # 3000 items
# result = pro.pledge_stat(end_date='20210723')
# print(result)


# result = pro.pledge_detail(ts_code='000014.SZ')
# print(result)

# result = pro.pledge_detail(ts_code='000014.SZ', start_date='20170101', end_date='20180101')
# print(result)           # start_date, end_date are useless


# result = pro.income_vip(period='20181231')
# print(result)
#
# result = pro.balancesheet_vip(period='20181231')
# print(result)
#
# result = pro.cashflow_vip(period='20181231')
# print(result)

# # Not support
# result = pro.fina_audit(ts_code='', period='20181231')
# print(result)


# result = pro.fina_mainbz(ts_code='000627.SZ')
# print(result)
# result = pro.fina_mainbz(ts_code='000627.SZ', type='P', start_date='19900101', end_date='20180726')
# print(result)
# result = pro.fina_mainbz(ts_code='000627.SZ', type='D', start_date='19900101', end_date='20180726')
# print(result)


# result = pro.concept_detail(ts_code='600848.SH', fields=[
#     'id', 'concept_name', 'ts_code', 'name', 'in_date', 'out_date'])
# print(result)


# # result = pro.top10_holders(start_date='20171231', end_date='20171231')
# # print(result)           # 5000 items
# result_stockholder_top_10 = pro.top10_holders(ts_code='600651.SH', start_date='19900101', end_date='20210101')
# print(result_stockholder_top_10)           # 1049 items
#
#
# # result = pro.top10_floatholders(start_date='20171231', end_date='20171231')
# # print(result)           # 5000 items
# result_stockholder_top_10_float = pro.top10_floatholders(ts_code='600651.SH', start_date='19900101', end_date='20210101')
# print(result_stockholder_top_10_float)           # 746 items
#
#
# # result = pro.stk_holdernumber(end_date='20171231')
# # print(result)
# result_stockholder_count = pro.stk_holdernumber(ts_code='600651.SH', start_date='19900101', end_date='20210101')
# print(result_stockholder_count)
#
# # ----------------------------------------------------------------------------------
#
# del result_stockholder_top_10['ts_code']
# convert_ts_date_field(result_stockholder_top_10, 'ann_date')
# convert_ts_date_field(result_stockholder_top_10, 'end_date')
# grouped_stockholder_top_10 = result_stockholder_top_10.groupby('end_date')
#
# data_dict = {'period': [], 'stockholder_top10': []}
# for g, df in grouped_stockholder_top_10:
#     data_dict['period'].append(g)
#     del df['end_date']
#     data_dict['stockholder_top10'].append(df.to_dict('records'))
# grouped_stockholder_top_10_df = pd.DataFrame(data_dict)
# grouped_stockholder_top_10_df['stock_identity'] = ts_code_to_stock_identity('600651.SH')
#
#
# del result_stockholder_top_10_float['ts_code']
# convert_ts_date_field(result_stockholder_top_10_float, 'ann_date')
# convert_ts_date_field(result_stockholder_top_10_float, 'end_date')
# grouped_stockholder_top_10_float = result_stockholder_top_10_float.groupby('end_date')
#
# data_dict = {'period': [], 'stockholder_top10': []}
# for g, df in grouped_stockholder_top_10_float:
#     data_dict['period'].append(g)
#     del df['end_date']
#     data_dict['stockholder_top10'].append(df.to_dict('records'))
# grouped_stockholder_top_10_float_df = pd.DataFrame(data_dict)
# grouped_stockholder_top_10_float_df['stock_identity'] = ts_code_to_stock_identity('600651.SH')
#
#
# convert_ts_code_field(result_stockholder_count)
# convert_ts_date_field(result_stockholder_count, 'ann_date')
# convert_ts_date_field(result_stockholder_count, 'end_date', 'period')
#
#
# result = pd.merge(grouped_stockholder_top_10_df, grouped_stockholder_top_10_float_df,
#                   on=['stock_identity', 'period'], how='outer')
# result = pd.merge(result, result_stockholder_count,
#                   on=['stock_identity', 'period'], how='outer')
# result = result.sort_values('period')
# print(result)

# -----------------------------------------------------------------------------------------------

# result = pro.stk_holdertrade(ann_date='20190426')
# print(result)

result = pro.stk_holdertrade(ts_code='000900.SZ')
print(result)





