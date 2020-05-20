#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2019/02/02
@file: DataTable.py
@function:
@modify:
"""
from os import path
import pandas as pd

from .SqlRw import SqlAccess
from ..Utiltity.common import *
from ..Utiltity.time_utility import *
from ..StockAnalysisSystem import StockAnalysisSystem


class XListTable:
    FIELD = ['name', 'reason', 'comments', 'last_update']
    INDEX_NAME = 0
    INDEX_REASON = 1
    INDEX_COMMENTS = 2
    INDEX_LAST_UPDATE = 3

    def __init__(self, table: str, sql_db: SqlAccess):
        assert table != ''
        self.__table = table
        self.__sql_db = sql_db
        self.__local_data = None

        self.reload()

    def clear(self):
        self.__local_data = pd.DataFrame(columns=XListTable.FIELD)

    def flush(self) -> bool:
        self.__local_data['last_update'] = pd.to_datetime(
            self.__local_data['last_update'], infer_datetime_format=True)
        result = self.__sql_db.DataFrameToDB(self.__table, self.__local_data)
        return result

    def reload(self):
        self.__local_data = self.__sql_db.DataFrameFromDB(self.__table, XListTable.FIELD, '')
        if self.__local_data is None:
            self.__local_data = pd.DataFrame(columns=XListTable.FIELD)

    def upsert_to_list(self, name: str, reason: str, comments: str = ''):
        self.remove_from_list(name)
        s = pd.Series([name, reason, comments, now()], index=XListTable.FIELD)
        self.__local_data = self.__local_data.append(s, ignore_index=True)

    def remove_from_list(self, name: str):
        name_field = XListTable.FIELD[XListTable.INDEX_NAME]
        df = self.__local_data
        df.drop(df[df[name_field] == name].index, inplace=True)

    def get_name_list(self) -> [str]:
        name_field = XListTable.FIELD[XListTable.INDEX_NAME]
        return self.__local_data[name_field].tolist()

    def get_name_table(self) -> pd.DataFrame:
        return self.__local_data

    def import_csv(self, csv_file: str, replace: bool = False) -> bool:
        df = pd.read_csv(csv_file, index_col=None)
        header = list(df.columns)
        if 'name' not in header or 'reason' not in header or 'comments' not in header:
            return False
        if replace:
            self.clear()

        data_utility = StockAnalysisSystem().get_data_hub_entry().get_data_utility()
        name_column = df['name'].values.tolist()
        id_column = data_utility.names_to_stock_identity(name_column)
        df['name'] = np.array(id_column)

        for index, row in df.iterrows():
            self.upsert_to_list(row['name'], row['reason'], row['comments'])
        return True




