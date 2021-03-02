import tushare as ts
from StockAnalysisSystem.core.DataHub.DataAgent import DataAgentUtility
from StockAnalysisSystem.core.DataHub.DataAgent import DataAgent
from StockAnalysisSystem.core.DataHub import DataAgentBuilder
from StockAnalysisSystem.core.UniversalDataDepot import DepotMongoDB
from pymongo import MongoClient


DATA_DURATION_QUARTER = 500
mongodb_client = MongoClient()

my_token = '022399ffd4fb40c10c8f5d6b634b0179f76fe6119298c5ed2656d7a8'
# 设置token
ts.set_token(my_token)

# 初始化pro接口
pro = ts.pro_api()

# 股票回购2021-01-01至2021-03-01数据
repurchase = pro.repurchase(ann_date='', start_date='20210101', end_date='20210301')

# # 获取单日
# df = pro.repurchase(ann_date='20181010')
print(repurchase)
print('***'*30)

# 限售股解禁 数据获取
share_float = pro.share_float(ann_date='20210222')
print(share_float)


data_repurchase = DataAgent(
    uri='Finance.IncomeStatement',
    depot=DepotMongoDB(primary_keys=['stock_identity', 'period'],
                       client=mongodb_client,
                       database='StockAnalysisSystem',
                       data_table=DataAgentBuilder.uri_to_table('Finance. IncomeStatement')),
    identity_field='stock_identity',
    datetime_field='period',
    data_duration=DATA_DURATION_QUARTER,
    update_list=DataAgentUtility.a_stock_list,
    ),

data_share_float = DataAgent(
    uri='Market. SecuritiesInfo',
    depot=DepotMongoDB(primary_keys='stock_identity',
                       client=mongodb_client,
                       database='StockAnalysisSystem',
                       data_table=DataAgentBuilder.uri_to_table('Market. SecuritiesInfo')),
    identity_field='stock_identity',
    datetime_field=None,
    data_duration=DATA_DURATION_QUARTER,
    update_priority=DataAgent.PRIORITY_HIGHEST
    ),































