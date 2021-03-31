import os
import datetime
import traceback
import pandas as pd

import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.api_util import ensure_dir
from StockAnalysisSystem.core.Utility.TagsLib import Tags
from StockAnalysisSystem.core.Utility.event_queue import Event
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext

from StockMemo.StockMemo import StockMemo
from StockMemo.BlackList import BlackList


# ----------------------------------------------------------------------------------------------------------------------

class StockMemoService:
    def __init__(self, sas_api: sasApi, memo_path: str):
        self.__sas_api: sasApi = sas_api
        self.__memo_path: str = memo_path

        print('==> Init stock memo with path: ' + memo_path)

        self.__stock_tags = Tags(os.path.join(memo_path, 'tags.json'))
        self.__stock_memo = StockMemo(os.path.join(memo_path, 'stock_memo.csv'))
        self.__black_list = BlackList(self.__stock_memo, self.__stock_tags)

    def update_root_path(self, root_path: str):
        self.__stock_tags.load(os.path.join(root_path, 'tags.json'))
        self.__stock_memo.raw_record().load(os.path.join(root_path, 'stock_memo.csv'))

    def register_sys_call(self):
        # Stock memo
        self.__sas_api.register_sys_call('stock_memo_save',             self.__stock_memo.stock_memo_save,              group='stock_memo')
        self.__sas_api.register_sys_call('stock_memo_load',             self.__stock_memo.stock_memo_load,              group='stock_memo')
        self.__sas_api.register_sys_call('stock_memo_filter_record',    self.__stock_memo.stock_memo_filter_record,     group='stock_memo')
        self.__sas_api.register_sys_call('stock_memo_get_record',       self.__stock_memo.stock_memo_get_record,        group='stock_memo')
        self.__sas_api.register_sys_call('stock_memo_add_record',       self.__stock_memo.stock_memo_add_record,        group='stock_memo')
        self.__sas_api.register_sys_call('stock_memo_update_record',    self.__stock_memo.stock_memo_update_record,     group='stock_memo')
        self.__sas_api.register_sys_call('stock_memo_delete_record',    self.__stock_memo.stock_memo_delete_record,     group='stock_memo')
        self.__sas_api.register_sys_call('stock_memo_get_all_security', self.__stock_memo.stock_memo_get_all_security,  group='stock_memo')

        # Stock memo tags
        self.__sas_api.register_sys_call('stock_memo_save_tags',            self.__stock_tags.save,                     group='stock_memo_tags')
        self.__sas_api.register_sys_call('stock_memo_load_tags',            self.__stock_tags.load,                     group='stock_memo_tags')
        self.__sas_api.register_sys_call('stock_memo_all_tags',             self.__stock_tags.all_tags,                 group='stock_memo_tags')
        self.__sas_api.register_sys_call('stock_memo_all_securities',       self.__stock_tags.all_objs,                 group='stock_memo_tags')
        self.__sas_api.register_sys_call('stock_memo_tags_of_securities',   self.__stock_tags.tags_of_objs,             group='stock_memo_tags')
        self.__sas_api.register_sys_call('stock_memo_securities_from_tags', self.__stock_tags.objs_from_tags,           group='stock_memo_tags')
        self.__sas_api.register_sys_call('stock_memo_set_security_tags',    self.__stock_tags.set_obj_tags,             group='stock_memo_tags')

        # Black list
        self.__sas_api.register_sys_call('save_black_list',             self.__black_list.save_black_list,              group='black_list')
        self.__sas_api.register_sys_call('in_black_list',               self.__black_list.in_black_list,                group='black_list')
        self.__sas_api.register_sys_call('all_black_list',              self.__black_list.all_black_list,               group='black_list')
        self.__sas_api.register_sys_call('add_to_black_list',           self.__black_list.add_to_black_list,            group='black_list')
        self.__sas_api.register_sys_call('remove_from_black_list',      self.__black_list.remove_from_black_list,       group='black_list')
        self.__sas_api.register_sys_call('get_black_list_data',         self.__black_list.get_black_list_data,          group='black_list')
        self.__sas_api.register_sys_call('save_black_list',             self.__black_list.reload_black_list_data,       group='black_list')


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': 'bd9a7d9f-dbcc-4dc8-8992-16dac9191ff9',
        'plugin_name': 'Stock Memo',
        'plugin_version': '0.0.0.1',
        'tags': ['stock_memo', 'Sleepy'],
    }


def plugin_adapt(method: str) -> bool:
    return method in ['bd9a7d9f-dbcc-4dc8-8992-16dac9191ff9']


def plugin_capacities() -> list:
    return ['api']


# ----------------------------------------------------------------------------------------------------------------------

stockMemoService: StockMemoService = None
subServiceContext: SubServiceContext = None


def init(sub_service_context: SubServiceContext) -> bool:
    try:
        global stockMemoService
        global subServiceContext

        subServiceContext = sub_service_context
        default_memo_path = os.path.join(os.getcwd(), 'StockMemo')
        memo_path = subServiceContext.sas_api.config().get('memo_path', default_memo_path)
        if not ensure_dir(memo_path):
            print('Check stock memo dir fail.')
            assert False
        stockMemoService = StockMemoService(subServiceContext.sas_api, memo_path)
        stockMemoService.register_sys_call()
    except Exception as e:
        import traceback
        print('Plugin-in init error: ' + str(e))
        print(traceback.format_exc())
    finally:
        pass
    return True


def startup() -> bool:
    return True

