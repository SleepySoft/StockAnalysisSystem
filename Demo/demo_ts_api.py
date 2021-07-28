import os
import tushare as ts
from StockAnalysisSystem.core.config import Config


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


result = pro.share_float(ts_code='603301.SH', start_date='20180402', end_date='20180411')
print(len(result))
print('%s - %s' % (min(result['ann_date']), max(result['ann_date'])))
print(result)


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
