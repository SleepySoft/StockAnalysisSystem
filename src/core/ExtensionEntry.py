import time
from threading import Thread
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget

from .StockAnalysisSystem import *
from .Utiltity.time_utility import *
from .Utiltity.plugin_manager import *


class ExtensionManager:
    class ExtensionThreadWrapper(Thread):
        def __init__(self, plugin: PluginManager, extension: any):
            super(ExtensionManager.ExtensionThreadWrapper, self).__init__()
            self.__plugin = plugin
            self.__extension = extension
            self.__context = {'quit_flag': False}

        def run(self):
            ret = self.__plugin.execute_module_function(self.__extension, 'thread', {'context': self.__context})
            print('Extension thread exit, return = ' + str(ret))

        def quit(self):
            self.__context['quit_flag'] = True

    def __init__(self, sas: StockAnalysisSystem, plugin: PluginManager):
        self.__sas = sas
        self.__plugin = plugin

        # Timer for update status
        self.__prev_tick = 0
        self.__timer = QTimer()
        self.__timer.setInterval(1000)
        self.__timer.timeout.connect(self.__poll_period_extensions)

        # Threads
        self.__extension_threads = {}

        self.__extension_cap = {}
        self.__period_extension = []
        self.__thread_extension = []
        self.__widget_extension = []

    def init(self) -> bool:
        self.__plugin.refresh()
        modules = self.__plugin.all_modules()
        for module in modules:
            result = self.__plugin.execute_module_function(module, 'plugin_capacities', {})
            if len(result) == 0:
                continue
            capacities = result[0]
            if capacities is not None and isinstance(capacities, (list, tuple)):
                if 'period' in capacities:
                    self.__period_extension.append(module)
                if 'thread' in capacities:
                    self.__thread_extension.append(module)
                if 'widget' in capacities:
                    self.__widget_extension.append(module)
                self.__extension_cap[module] = capacities
        return self.init_extensions() and self.activate_extensions()

    def init_extensions(self) -> bool:
        fail_extension = []
        for extension in self.__extension_cap.keys():
            result = self.__plugin.execute_module_function(extension, 'init', {'sas': self.__sas})
            if len(result) == 0 or not result[0]:
                fail_extension.append(extension)
                capacity = self.__extension_cap.get(extension, {})
                print('Fail to init extension: ' + capacity.get('plugin_id', 'NO ID'))
        for fail_ext in fail_extension:
            del self.__extension_cap[fail_ext]
            if fail_ext in self.__period_extension:
                self.__period_extension.remove(fail_ext)
            if fail_ext in self.__thread_extension:
                self.__thread_extension.remove(fail_ext)
            if fail_ext in self.__widget_extension:
                self.__widget_extension.remove(fail_ext)
        return True

    def activate_extensions(self) -> bool:
        self.__timer.start()
        self.__run_thread_extensions()
        return True

    def create_extensions_widgets(self, parent: QWidget) -> list:
        widgets = []
        for extension in self.__widget_extension:
            result = self.__plugin.execute_module_function(extension, 'widget', {'parent': parent})
            if len(result) > 0 and result[0] is not None:
                widgets.append(result[0])
        return widgets

    # ------------------------------------------------------------------------------------------------

    def __run_thread_extensions(self) -> bool:
        for extension in self.__thread_extension:
            extension_thread = ExtensionManager.ExtensionThreadWrapper(self.__plugin, extension)
            self.__extension_threads[extension] = extension_thread
            extension_thread.start()
        return True

    def __poll_period_extensions(self) -> bool:
        tick_ns = time.time() * 1000000
        if self.__prev_tick == 0:
            self.__prev_tick = tick_ns
        elapsed_ns = tick_ns - self.__prev_tick
        for extension in self.__period_extension:
            self.__plugin.execute_module_function(extension, 'period', {'interval_ns': elapsed_ns})
        self.__prev_tick = tick_ns
        return True






