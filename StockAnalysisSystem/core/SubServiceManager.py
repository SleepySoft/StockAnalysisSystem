import time
from threading import Thread
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget

import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.event_queue import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.Utility.plugin_manager import *


class SubServiceManager:
    class SubServiceEventWrapper(Event):
        def __init__(self, plugin: PluginManager, identity: str, extension):
            self.__plugin = plugin
            self.__identity = identity
            self.__extension = extension
            super(SubServiceManager.SubServiceEventWrapper, self).__init__()

        def identity(self) -> str:
            return self.__identity

        def handle_event(self, event: Event):
            self.__plugin.execute_module_function(self.__extension, 'event_handler', {'event': event})

    class SubServiceThreadWrapper(Thread):
        def __init__(self, plugin: PluginManager, extension: any):
            super(ExtensionManager.SubServiceThreadWrapper, self).__init__()
            self.__plugin = plugin
            self.__service = extension
            self.__context = {'quit_flag': False}

        def run(self):
            ret = self.__plugin.execute_module_function(self.__service, 'thread', {'context': self.__context})
            print('Sub Service thread exit, return = ' + str(ret))

        def quit(self):
            self.__context['quit_flag'] = True

    def __init__(self, sas_api: sasApi, plugin: PluginManager):
        self.__sas_api = sas_api
        self.__plugin = plugin

        self.__event_queue = EventQueue()

        # Threads
        self.__service_threads = {}

        self.__service_cap = {}
        self.__period_service = []
        self.__thread_service = []
        self.__event_handler_service = []

    def init(self) -> bool:
        self.__plugin.refresh()
        modules = self.__plugin.all_modules()
        for module in modules:
            result = self.__plugin.execute_module_function(module, 'plugin_capacities', {})
            if len(result) == 0:
                continue
            capacities = result[0]
            if capacities is not None and isinstance(capacities, (list, tuple)):
                if 'thread' in capacities:
                    self.__thread_service.append(module)
                if 'polling' in capacities:
                    self.__period_service.append(module)
                if 'event_handler' in capacities:
                    self.__event_handler_service.append(module)
                self.__service_cap[module] = capacities
        return self.init_services() and self.activate_services()

    def init_services(self) -> bool:
        fail_service = []
        for extension in self.__service_cap.keys():
            result = self.__plugin.execute_module_function(extension, 'init', {'sas_api': self.__sas_api})
            if len(result) == 0 or not result[0]:
                fail_service.append(extension)
                capacity = self.__service_cap.get(extension, {})
                if isinstance(capacity, dict):
                    print('Fail to init extension: ' + capacity.get('plugin_id', 'NO ID'))
                else:
                    print('Fail to init extension: prob data error')
        for fail_ext in fail_service:
            del self.__service_cap[fail_ext]
            if fail_ext in self.__period_service:
                self.__period_service.remove(fail_ext)
            if fail_ext in self.__thread_service:
                self.__thread_service.remove(fail_ext)
            if fail_ext in self.__event_handler_service:
                self.__event_handler_service.remove(fail_ext)
        return True

    def activate_services(self) -> bool:
        self.__timer.start()
        self.__run_thread_services()
        return True

    def drive_service(self):
        pass

    # ------------------------------------------------------------------------------------------------

    def __register_event_handler_service(self) -> bool:
        for extension in self.__event_handler_service:
            self.__event_queue.add_event_handler(SubServiceManager.SubServiceEventWrapper(extension))

    def __run_thread_services(self) -> bool:
        for extension in self.__thread_service:
            extension_thread = ExtensionManager.SubServiceThreadWrapper(self.__plugin, extension)
            self.__service_threads[extension] = extension_thread
            extension_thread.start()
        return True

    def __poll_period_services(self) -> bool:
        tick_ns = time.time() * 1000000
        if self.__prev_tick == 0:
            self.__prev_tick = tick_ns
        elapsed_ns = tick_ns - self.__prev_tick
        for extension in self.__period_service:
            self.__plugin.execute_module_function(extension, 'period', {'interval_ns': elapsed_ns})
        self.__prev_tick = tick_ns
        return True






