import datetime
import os
import pandas as pd

from .StockMemo.StockMemo import StockMemo
from .StockMemo.BlackList import BlackList
from StockAnalysisSystem.core.Utility.TagsLib import Tags
import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.event_queue import Event


# ----------------------------------------------------------------------------------------------------------------------


class StockMemoService:
    def __init__(self, sas_api: sasApi, root_path: str):
        self.__sas_api: sasApi = sas_api
        self.__root_path: str = root_path
        self.__stock_tags = Tags(os.path.join(root_path, 'tags.json'))
        self.__stock_memo = StockMemo(os.path.join(root_path, 'stock_memo.csv'))
        self.__black_list = BlackList(self.__stock_memo, self.__stock_tags)

    def update_root_path(self, root_path: str):
        self.__stock_tags.load(os.path.join(root_path, 'tags.json'))
        self.__stock_memo.raw_record().load(os.path.join(root_path, 'stock_memo.csv'))

    def register_sys_call(self):
        # Stock memo
        self.__sas_api.register_sys_call('stock_memo_save',             self.__stock_memo.stock_memo_save,              group='stock_memo')
        self.__sas_api.register_sys_call('stock_memo_load',             self.__stock_memo.stock_memo_load,              group='stock_memo')
        self.__sas_api.register_sys_call('stock_memo_get_record',       self.__stock_memo.stock_memo_get_record,        group='stock_memo')
        self.__sas_api.register_sys_call('stock_memo_add_record',       self.__stock_memo.stock_memo_add_record,        group='stock_memo')
        self.__sas_api.register_sys_call('stock_memo_update_record',    self.__stock_memo.stock_memo_update_record,     group='stock_memo')
        self.__sas_api.register_sys_call('stock_memo_delete_record',    self.__stock_memo.stock_memo_delete_record,     group='stock_memo')
        self.__sas_api.register_sys_call('get_stock_memo_all_security', self.__stock_memo.get_stock_memo_all_security,  group='stock_memo')

        # Black list
        self.__sas_api.register_sys_call('save_black_list',         self.__black_list.save_black_list,          group='black_list')
        self.__sas_api.register_sys_call('in_black_list',           self.__black_list.in_black_list,            group='black_list')
        self.__sas_api.register_sys_call('all_black_list',          self.__black_list.all_black_list,           group='black_list')
        self.__sas_api.register_sys_call('add_to_black_list',       self.__black_list.add_to_black_list,        group='black_list')
        self.__sas_api.register_sys_call('remove_from_black_list',  self.__black_list.remove_from_black_list,   group='black_list')
        self.__sas_api.register_sys_call('get_black_list_data',     self.__black_list.get_black_list_data,      group='black_list')
        self.__sas_api.register_sys_call('save_black_list',         self.__black_list.reload_black_list_data,   group='black_list')


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
    return [
        'period',
        'thread',
        'on_event'
    ]


# ----------------------------------------------------------------------------------------------------------------------

sasApiEntry: sasApi = None
stockMemoService: StockMemoService = None


def init(sas_api: sasApi) -> bool:
    """
    System will invoke this function at startup once.
    :param sas_api: The sasApi entry
    :return: True if successful else False
    """
    try:
        global sasApiEntry
        global stockMemoService

        sasApiEntry = sas_api
        stockMemoService = StockMemoService(sasApi)
    except Exception as e:
        pass
    finally:
        pass
    return True


def period(interval_ns: int):
    """
    If you specify 'period' in plugin_capacities(). This function will be invoked periodically by MAIN thread,
        the invoke interval should be more or less than 100ms.
    Note that if this extension spends too much time on this function. The interface will be blocked.
    And this extension will be removed from running list.
    :param interval_ns: The interval between previous invoking and now.
    :return: None
    """
    print('Period...' + str(interval_ns))
    pass


def thread(context: dict):
    """
    If you specify 'thread' in plugin_capacities(). This function will be invoked in a thread.
    If this function returns or has uncaught exception, the thread will be terminated and will not restart again.
    :param context: The context from StockAnalysisSystem, includes:
                    'quit_flag': bool - Process should be terminated and quit this function if it's True.
                    '?????????': any  - TBD
    :return: None
    """
    print('Thread...')
    pass


def on_event(event: Event, **kwargs):
    """
    Use this function to handle event. Includes timer and subscribed event.
    :param event: The event data
    :return:
    """
    print('Event')
    pass











