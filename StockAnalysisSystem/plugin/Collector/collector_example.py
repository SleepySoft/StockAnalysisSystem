import pandas as pd
from datetime import datetime
# import tushare as ts
# from pymongo import MongoClient
#
#
# mongodb_client = MongoClient()
# my_token = '022399ffd4fb40c10c8f5d6b634b0179f76fe6119298c5ed2656d7a8'
# # 设置token
# ts.set_token(my_token)
#
# # 初始化pro接口
# pro = ts.pro_api()
#
# # 股票回购2021-01-01至2021-03-01数据
# repurchase = pro.repurchase(ann_date='', start_date='20210101', end_date='20210301')
# # print(type(repurchase))


# def get_data(data):
#     return {'uri': data}
flog = 'Example.Collector'


def plugin_prob() -> dict:
    return {
        'plugin_name': 'dummy_plugin_for_test',
        'plugin_version': '0.0.0.1',
        'tags': ['example', 'collector']
    }


def plugin_adapt(uri: str) -> bool:
    return uri == flog


def plugin_capacities() -> list:
    return [
        flog,
    ]


def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri == flog:
        return pd.DataFrame({
            'ibd': ['300783.SZ', '1StockA', '2StockB', 'StockB', 'StockC', 'StockC'],
            'time2': [datetime(1995, 1, 1), datetime(1996, 1, 1),    # StockA
                     datetime(2002, 2, 1), datetime(2005, 5, 1),    # StockB
                     datetime(2020, 3, 1), datetime(2021, 1, 1)],   # StockC
            'field11': [100., 20., 30., 40., 500., 600.],
            'field22': ['A', 'B', 'C', 'D', 'E', 'F'],
        })
    else:
        return None


def validate(**kwargs) -> bool:
    pass
    return True


def fields() -> dict:
    return {}



















































