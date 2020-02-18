#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2019/02/02
@file: ColumnTable.py
@function:
@modify:
"""


from Database.DatabaseEntry import DatabaseEntry


class ColumnTable:
    COLUMN_TABLE_FIELD = ['column_name', 'column_index']

    def __init__(self, table_name: str):
        self.__table_name = table_name
        self.__column_name_index_table = {}

    def Init(self, auto: bool) -> bool:
        if auto:
            if not self.LoadFromDB():
                print('Error: Load Column Table [' + self.__table_name + '] Fail!')
                return False
        return True

    def Reset(self):
        self.__column_name_index_table = {}

    def GetTableName(self) -> str:
        return self.__table_name

    def AddColumn(self, column_name: str) -> int:
        if column_name not in self.__column_name_index_table.keys():
            index = self.__assign_new_index()
            self.__column_name_index_table[column_name] = index
        else:
            index = self.__column_name_index_table[column_name]
        self.DumpToDB()
        return index

    def DelColumn(self, column_name: str):
        if column_name in self.__column_name_index_table.keys():
            del self.__column_name_index_table[column_name]
            self.DumpToDB()

    def UpdateColumn(self, column_name_old: str, column_name_new: str) -> bool:
        if column_name_new in self.__column_name_index_table.keys():
            return False
        if column_name_old not in self.__column_name_index_table.keys():
            return False
        index = self.__column_name_index_table[column_name_old]
        del self.__column_name_index_table[column_name_old]
        self.__column_name_index_table[column_name_new] = index
        return True

    def GetColumnIndex(self, column_name: str) -> int:
        return self.__column_name_index_table[column_name] if column_name in self.__column_name_index_table else -1

    def ColumnsToIndex(self, column_names: [str]) -> [str]:
        return [self.AddColumn(column_name) for column_name in column_names]

    def GetColumnNameIndexTable(self) -> dict:
        return self.__column_name_index_table

    # --------------------------------------------------- Load/Save ---------------------------------------------------

    def LoadFromDB(self) -> bool:
        self.Reset()
        self.__column_name_index_table = DatabaseEntry().get_utility_db().DictFromDB(
            self.__table_name, ColumnTable.COLUMN_TABLE_FIELD)
        return True

    def DumpToDB(self) -> bool:
        return DatabaseEntry().get_utility_db().DictToDB(
            self.__table_name, self.__column_name_index_table, ColumnTable.COLUMN_TABLE_FIELD)

    def __assign_new_index(self) -> int:
        index = 0
        while index in self.__column_name_index_table.values():
            index += 1
        return index

