import tushare as ts
from pymongo import MongoClient
import pandas as pd
from zs import data_config as dc
pd.set_option('display.max_columns', 1500)  # 显示500条列数据中间无  ...  省略数据
pd.set_option('display.max_rows', 1500)     # 显示500条行数据中间无 ... 省略数据
pd.set_option('display.width', 1500)


class TsData(object):
    """ts数据获取"""
    def __init__(self):
        self.mongodb_client = MongoClient()
        self.my_token = '022399ffd4fb40c10c8f5d6b634b0179f76fe6119298c5ed2656d7a8'
        # 设置token
        ts.set_token(self.my_token)
        # 初始化pro接口
        self.pro = ts.pro_api()

    @staticmethod
    def repurchase_get_data() -> pd.DataFrame or None:
        # 获取股票回购数据
        return TsData().pro.repurchase(ann_date='', start_date=dc.repurchase_start, end_date=dc.repurchase_end)

    @staticmethod
    def share_float_get_data() -> pd.DataFrame or None:
        # 获取限售股解禁数据
        return TsData().pro.share_float(ann_date=dc.share_float_ann_date)










