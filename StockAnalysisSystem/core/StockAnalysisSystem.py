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
import errno

from .Utility.common import *
from .Utility.task_queue import *
from .Utility.time_utility import *


class StockAnalysisSystem(metaclass=ThreadSafeSingleton):
    def __init__(self):
        self.__inited = False
        self.__quit_lock = 0
        self.__log_errors = []

        # Root path is the contain folder of "core" folder
        self.__root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Project is the work path of sas service. All the file load/dump/generate operation are default in this path.
        # Project path is the parent path of the root path by default, which is the root path of this project.
        self.__project_path = os.path.dirname(self.__root_path)

        self.__config = None
        self.__task_queue = TaskQueue()

        self.__plugin_table = {}

        self.__data_hub_entry = None
        self.__strategy_entry = None
        self.__database_entry = None
        self.__factor_center = None

        self.__sub_service_manager = None
        # self.__extension_manager = None

        self.__sys_call = None

    # ----------------------------------------- Path -----------------------------------------

    def get_root_path(self) -> str:
        return self.__root_path

    def get_project_path(self) -> str:
        return self.__project_path

    def set_project_path(self, project_path: str):
        """
        Must config project path before check_initialize()
        :param project_path: The project path.
        :return: None
        """
        self.__project_path = project_path

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

    def check_initialize(self, project_path: str = '', config=None, not_load_config: bool = False) -> bool:
        if self.__inited:
            return True

        from StockAnalysisSystem.core.Utility.syscall import SysCall
        self.__sys_call = SysCall()

        if str_available(project_path):
            self.__project_path = project_path
        else:
            print('Warning: Project path is not available. Please provide a available path in program initialization.')
        print('Initializing Stock Analysis System with project path : ' + project_path)

        sqlite_data_path = os.path.join(self.get_project_path(), 'Data')
        config_file_path = os.path.join(self.get_project_path(), 'config.json')

        # try:
        #     os.makedirs(sqlite_data_path)
        # except OSError as e:
        #     if e.errno != errno.EEXIST:
        #         print('Build sqlite data path: %s FAIL' % sqlite_data_path)
        # finally:
        #     pass

        clock = Clock()
        self.__log_errors = []

        from .config import Config
        from .DataHubEntry import DataHubEntry
        from .AnalyzerEntry import StrategyEntry
        from .Database.DatabaseEntry import DatabaseEntry
        from .Utility.plugin_manager import PluginManager

        if isinstance(config, Config):
            self.__config = config
        else:
            self.__config = Config()
        if not_load_config:
            pass
        else:
            if not self.__config.load_config(config_file_path):
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

        self.__database_entry = DatabaseEntry()

        if not self.__database_entry.config_sql_db(sqlite_data_path):
            self.__log_errors.append('Config SQL database fail, maybe the sqlite data path not exits...Ignore')
            # Just ignore it.
            # return False

        if not self.__database_entry.config_nosql_db(self.__config.get('NOSQL_DB_HOST'),
                                                     self.__config.get('NOSQL_DB_PORT'),
                                                     self.__config.get('NOSQL_DB_USER'),
                                                     self.__config.get('NOSQL_DB_PASS')):
            self.__log_errors.append('Config NoSql database fail.')
            return False

        factor_plugin = PluginManager()
        strategy_plugin = PluginManager()
        collector_plugin = PluginManager()
        # extension_plugin = PluginManager()
        sub_service_plugin = PluginManager()

        self.__plugin_table['Factor'] = factor_plugin
        self.__plugin_table['Analyzer'] = strategy_plugin
        self.__plugin_table['Collector'] = collector_plugin
        # self.__plugin_table['Extension'] = extension_plugin
        self.__plugin_table['SubService'] = sub_service_plugin

        default_plugin_path = os.path.join(self.get_root_path(), 'plugin')
        project_plugin_path = os.path.join(self.get_project_path(), 'plugin')

        # Import default plugin
        if os.path.isdir(default_plugin_path):
            print('Load default plugin.')
            factor_plugin.add_plugin_path(os.path.join(default_plugin_path, 'Factor'))
            strategy_plugin.add_plugin_path(os.path.join(default_plugin_path, 'Analyzer'))
            collector_plugin.add_plugin_path(os.path.join(default_plugin_path, 'Collector'))
            # extension_plugin.add_plugin_path(os.path.join(default_plugin_path, 'Extension'))
            sub_service_plugin.add_plugin_path(os.path.join(default_plugin_path, 'SubService'))
        else:
            print('Default plugin not found.')

        if os.path.isdir(project_plugin_path) and project_plugin_path != default_plugin_path:
            print('Load project plugin.')
            factor_plugin.add_plugin_path(os.path.join(project_plugin_path, 'Factor'))
            strategy_plugin.add_plugin_path(os.path.join(project_plugin_path, 'Analyzer'))
            collector_plugin.add_plugin_path(os.path.join(project_plugin_path, 'Collector'))
            # extension_plugin.add_plugin_path(os.path.join(project_plugin_path, 'Extension'))
            sub_service_plugin.add_plugin_path(os.path.join(project_plugin_path, 'SubService'))

        factor_plugin.refresh()
        strategy_plugin.refresh()
        collector_plugin.refresh()
        sub_service_plugin.refresh()

        # Because the ExtensionManager will refresh it.
        # extension_plugin.refresh()

        self.__data_hub_entry = DataHubEntry(self.__database_entry, collector_plugin, self.__config)
        self.__strategy_entry = StrategyEntry(strategy_plugin, self.__data_hub_entry, self.__database_entry)

        from .FactorEntry import FactorCenter
        self.__factor_center = FactorCenter(self.__data_hub_entry, self.__database_entry, factor_plugin)
        self.__factor_center.reload_plugin()
        # TODO: Refactor
        self.__data_hub_entry.get_data_center().set_factor_center(self.__factor_center)

        # TODO: Separate extension ui and data
        # from .ExtensionEntry import ExtensionManager
        # self.__extension_manager = ExtensionManager(self, extension_plugin)
        # self.__extension_manager.init()

        import StockAnalysisSystem.core.api as sasApi
        from .SubServiceManager import SubServiceManager
        self.__sub_service_manager = SubServiceManager(sasApi, sub_service_plugin)
        self.__sub_service_manager.init()

        print('Stock Analysis System Initialization Done, Time spending: ' + str(clock.elapsed_ms()) + ' ms')
        self.__inited = True

        # ------------------------------------------------------------------------------------
        # Debug: Print loggers
        # Note that service threads may add new loggers
        # ------------------------------------------------------------------------------------

        print('-' * 50)
        print('Existing loggers: ')
        print()
        for name in logging.root.manager.loggerDict:
            print(name)
        print('-' * 50)

        # ------------------------------------------------------------------------------------
        # Mark init as finished, then we can start threads and other components that depends on sasApi
        #    Because thread may reference this singleton, which may trigger init() again.
        #    Or the components that depends on sasApi but gets not inited flag.
        # ------------------------------------------------------------------------------------

        self.__task_queue.start()
        self.__sub_service_manager.startup()
        self.__sub_service_manager.run_service()

        return True

    def finalize(self):
        self.__task_queue.quit()
        self.__task_queue.join(5)

    # -------------------------------------------- Entry --------------------------------------------

    def get_sys_call(self):
        return self.__sys_call

    def get_plugin_manager(self, name: str):
        if name not in self.__plugin_table:
            print('Warning: the plugin manager name should be one of: ' + str(self.__plugin_table.keys()))
            return None
        return self.__plugin_table.get(name, None)

    def get_database_entry(self):
        return self.__database_entry if self.check_initialize() else None

    def get_data_hub_entry(self):
        return self.__data_hub_entry if self.check_initialize() else None

    def get_strategy_entry(self):
        return self.__strategy_entry if self.check_initialize() else None

    # def get_extension_manager(self):
    #     return self.__extension_manager if self.check_initialize() else None

    def get_factor_center(self):
        return self.__factor_center if self.check_initialize() else None

    # # -------------------------------------------- SysCall --------------------------------------------
    #
    # def sys_call(self, name: str, *args, **kwargs) -> any:
    #     register_entry = self.__sys_call.get(name, None)
    #     if register_entry is None:
    #         print('Warning: No sys call named: ' + name)
    #         return None
    #     else:
    #         if not isinstance(register_entry, (list, tuple)) or len(register_entry) != 3 or register_entry[0] is None:
    #             return None
    #         else:
    #             return register_entry[0](*args, **kwargs)
    #
    # def register_sys_call(self, name: str, parameters: dict, comments: str, entry, replace: bool = False) -> bool:
    #     if name in self.__sys_call.keys():
    #         if replace:
    #             print('Sys call %s already exists - replace.' % name)
    #         else:
    #             print('Sys call %s already exists - ignore.' % name)
    #             return False
    #     self.__sys_call[name] = (entry, parameters, comments)
    #     return True
    #
    # def unregister_sys_call(self, name: str):
    #     if name in self.__sys_call.keys():
    #         del self.__sys_call[name]



