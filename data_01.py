import tushare as ts
from pymongo import MongoClient
import pandas as pd
pd.set_option('display.max_columns', 1500)  # 显示500条列数据中间无  ...  省略数据
pd.set_option('display.max_rows', 1500)     # 显示500条行数据中间无 ... 省略数据
pd.set_option('display.width', 1500)

mongodb_client = MongoClient()
my_token = '022399ffd4fb40c10c8f5d6b634b0179f76fe6119298c5ed2656d7a8'
# 设置token
ts.set_token(my_token)

# 初始化pro接口
pro = ts.pro_api()

# 股票回购2021-01-01至2021-03-01数据
repurchase = pro.repurchase(ann_date='', start_date='20210101', end_date='20210301')
print(repurchase)


















