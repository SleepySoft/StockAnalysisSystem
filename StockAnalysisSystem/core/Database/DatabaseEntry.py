# !usr/bin/env python
# -*- coding:utf-8 -*-

"""
@version:
author:Sleepy
@time: 2019/01/08
@file: DatabaseEntry.py
@function:
@modify:
"""
import traceback
from os import path
from pymongo import MongoClient

from .SqlRw import SqlAccess
from .NoSqlRw import ItkvTable
from ..Utiltity.common import *


class DatabaseEntry:
    def __init__(self):
        self.__mongo_db_host = 'localhost'
        self.__mongo_db_port = '27017'
        self.__mongo_db_user = ''
        self.__mongo_db_pass = ''
        self.__sqlite_db_file = ''

        self.__mongo_db_url = ''
        self.__sql_db_access = None
        self.__mongo_db_client = None

        self.__no_sql_tables = {}

        self.__alias_table = None
        self.__update_table = None

        self.__gray_table = None
        self.__focus_table = None
        self.__black_table = None

    # ------------------------------------------------------------------------------------------------------------------

    def config_sql_db(self, db_path: str) -> bool:
        self.__sqlite_db_file = path.join(db_path, 'sAsUtility.db')
        self.__sql_db_access = SqlAccess(self.__sqlite_db_file)
        conn = self.__sql_db_access.BuildConnection()
        if conn is not None:
            conn.close()

            # import Database.AliasTable as AliasTable
            from .XListTable import XListTable
            # import Database.UpdateTableEx as UpdateTableEx

            # self.__alias_table = AliasTable.AliasTable(self.__sql_db_access)
            # self.__update_table = UpdateTableEx.UpdateTableEx(self.__sql_db_access)

            self.__gray_table = XListTable('gray_table', self.__sql_db_access)
            self.__focus_table = XListTable('focus_table', self.__sql_db_access)
            self.__black_table = XListTable('black_table', self.__sql_db_access)

            return True
        else:
            self.__alias_table = None
            self.__update_table = None

            self.__gray_table = None
            self.__focus_table = None
            self.__black_table = None

            return False

    def config_nosql_db(self, host: str, port: str, user: str, password: str) -> bool:
        self.__mongo_db_host = host
        self.__mongo_db_port = port
        self.__mongo_db_user = user
        self.__mongo_db_pass = password

        if self.__mongo_db_user != '':
            url = 'mongodb://%s:%s@%s:%s/' % (self.__mongo_db_user, self.__mongo_db_pass,
                                              self.__mongo_db_host, self.__mongo_db_port)
        else:
            url = 'mongodb://%s:%s/' % (self.__mongo_db_host, self.__mongo_db_port)

        try:
            self.__mongo_db_client = MongoClient(url,
                                                 maxPoolSize=50,
                                                 serverSelectionTimeoutMS=5000,
                                                 waitQueueTimeoutMS=1000)
            self.__mongo_db_client.server_info()

            from .UpdateTableEx import UpdateTableEx
            self.__update_table = UpdateTableEx(self.__mongo_db_client)

            return True
        except Exception as e:
            print('Mongodb config error.')
            print(e)
            print(traceback.format_exc())
            self.__mongo_db_client = None
            return False
        finally:
            pass

    # ------------------------------------------------- Database Entry -------------------------------------------------

    def get_utility_db(self) -> SqlAccess:
        return self.__sql_db_access

    def get_mongo_db_client(self) -> MongoClient:
        return self.__mongo_db_client

    # ------------------------------------------------- SQL Table Entry ------------------------------------------------

    def get_alias_table(self):
        return self.__alias_table

    def get_update_table(self):
        return self.__update_table

    def get_gray_table(self):
        return self.__gray_table

    def get_focus_table(self):
        return self.__focus_table

    def get_black_table(self):
        return self.__black_table

    # ------------------------------------------------ NoSQL Table Entry -----------------------------------------------

    def query_nosql_table(self, db: str, table: str,
                          identity_field: str = 'Identity',
                          datetime_field: str = 'DateTime') -> ItkvTable or None:
        if self.get_mongo_db_client() is None:
            return None
        if db not in self.__no_sql_tables.keys():
            self.__no_sql_tables[db] = {}
        database = self.__no_sql_tables.get(db)
        if table not in database.keys():
            database[table] = ItkvTable(self.get_mongo_db_client(), db, table, identity_field, datetime_field)
        return database.get(table, None)

