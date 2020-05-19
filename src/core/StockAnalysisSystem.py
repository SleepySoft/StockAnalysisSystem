#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:YuQiu
@time: 2017/08/08
@file: stock_analysis_system.py
@function:
@modify:
"""

import os

from .Utiltity.common import *
from .Utiltity.task_queue import *
from .Utiltity.time_utility import *


class StockAnalysisSystem(metaclass=ThreadSafeSingleton):
    def __init__(self):
        self.__inited = False
        self.__quit_lock = 0
        self.__log_errors = []

        from .config import Config
        self.__config = Config()
        self.__task_queue = TaskQueue()

        self.__factor_plugin = None
        self.__strategy_plugin = None
        self.__collector_plugin = None
        self.__extension_plugin = None

        self.__data_hub_entry = None
        self.__strategy_entry = None
        self.__database_entry = None
        self.__factor_center = None

        self.__extension_manager = None

    # ---------------------------------------- Config ----------------------------------------

    def get_config(self):
        return self.__config

    def get_log_errors(self) -> [str]:
        return self.__log_errors

    # ------------------------------------- System Task -------------------------------------

    def get_task_queue(self) -> TaskQueue:
        return self.__task_queue

    def can_sys_quit(self) -> bool:
        return (not self.__task_queue.is_busy()) and (self.__quit_lock == 0)

    def lock_sys_quit(self):
        self.__quit_lock += 1

    def release_sys_quit(self):
        self.__quit_lock = max(0, self.__quit_lock - 1)

    # ----------------------------------------- Init -----------------------------------------

    def is_initialized(self) -> bool:
        return self.__inited

    def check_initialize(self) -> bool:
        if self.__inited:
            return True

        print('Initializing Stock Analysis System ...')

        clock = Clock()
        self.__log_errors = []
        root_path = os.path.dirname(os.path.abspath(__file__))

        from .DataHubEntry import DataHubEntry
        from .StrategyEntry import StrategyEntry
        from .Database.DatabaseEntry import DatabaseEntry
        from .Utiltity.plugin_manager import PluginManager

        if not self.__config.load_config(os.path.join(root_path, 'config.json')):
            self.__log_errors.append('Load config fail.')
            return False

        ok, reason = self.__config.check_config()
        if not ok:
            self.__log_errors.append(reason)
            return False

        proxy_protocol = self.__config.get('PROXY_PROTOCOL')
        proxy_host = self.__config.get('PROXY_HOST')
        if str_available(proxy_protocol):
            if str_available(proxy_host):
                os.environ[proxy_protocol] = proxy_host
                print('Set proxy: %s = %s' % (proxy_protocol, proxy_host))
            else:
                os.environ[proxy_protocol] = ''
                print('Clear proxy: %s' % proxy_protocol)

        self.__database_entry = DatabaseEntry.DatabaseEntry()

        if not self.__database_entry.config_sql_db(os.path.join(root_path, 'Data')):
            self.__log_errors.append('Config SQL database fail.')
            return False

        if not self.__database_entry.config_nosql_db(self.__config.get('NOSQL_DB_HOST'),
                                                     self.__config.get('NOSQL_DB_PORT'),
                                                     self.__config.get('NOSQL_DB_USER'),
                                                     self.__config.get('NOSQL_DB_PASS')):
            self.__log_errors.append('Config NoSql database fail.')
            return False

        self.__factor_plugin = PluginManager(os.path.join(root_path, 'Factor'))
        self.__strategy_plugin = PluginManager(os.path.join(root_path, 'Analyzer'))
        self.__collector_plugin = PluginManager(os.path.join(root_path, 'Collector'))
        self.__extension_plugin = PluginManager(os.path.join(root_path, 'Extension'))

        self.__factor_plugin.refresh()
        self.__strategy_plugin.refresh()
        self.__collector_plugin.refresh()
        # self.__extension_plugin.refresh()

        self.__data_hub_entry = DataHubEntry(self.__database_entry, self.__collector_plugin)
        self.__strategy_entry = StrategyEntry(self.__strategy_plugin,
                                                            self.__data_hub_entry, self.__database_entry)

        from .FactorEntry import FactorCenter
        self.__factor_center = FactorCenter(self.__data_hub_entry, self.__database_entry, self.__factor_plugin)
        self.__factor_center.reload_plugin()
        # TODO: Refactor
        self.__data_hub_entry.get_data_center().set_factor_center(self.__factor_center)

        from .ExtensionEntry import ExtensionManager
        self.__extension_manager = ExtensionManager(self, self.__extension_plugin)
        self.__extension_manager.init()

        self.__task_queue.start()

        print('Stock Analysis System Initialization Done, Time spending: ' + str(clock.elapsed_ms()) + ' ms')
        self.__inited = True
        return True

    def finalize(self):
        self.__task_queue.quit()
        self.__task_queue.join(5)

    # -------------------------------------------- Entry --------------------------------------------

    def get_database_entry(self):
        return self.__database_entry if self.check_initialize() else None

    def get_data_hub_entry(self):
        return self.__data_hub_entry if self.check_initialize() else None

    def get_strategy_entry(self):
        return self.__strategy_entry if self.check_initialize() else None

    def get_extension_manager(self):
        return self.__extension_manager if self.check_initialize() else None

    def get_factor_center(self):
        return self.__factor_center if self.check_initialize() else None






