import time
import uuid
from functools import partial
from threading import Thread

import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.event_queue import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.Utility.plugin_manager import *


class SubServiceContext:
    def __init__(self):
        self.sas_api = None
        self.sub_service_manager = None
        self.extra_data = {}


class SubServiceManager:
    class SubServiceThreadWrapper(Thread):
        def __init__(self, extension: PluginWrapper):
            super(SubServiceManager.SubServiceThreadWrapper, self).__init__()
            self.__context = {'quit_flag': False}
            self.__extension = extension

        def run(self):
            ret = self.__extension.thread(context=self.__context)
            print('Sub Service thread exit, return = ' + str(ret))

        def quit(self):
            self.__context['quit_flag'] = True

    class SubServiceEventWrapper(EventHandler):
        def __init__(self, identity: str, extension: PluginWrapper):
            self.__identity = identity
            self.__extension = extension
            super(SubServiceManager.SubServiceEventWrapper, self).__init__()

        def identity(self) -> str:
            return self.__identity

        def handle_event(self, event: Event):
            self.__extension.event_handler(event=event)

    def __init__(self, sas_api: sasApi, plugin: PluginManager):
        self.__sas_api = sas_api
        self.__plugin = plugin

        self.__event_queue = EventQueue()

        self.__sub_service_context = SubServiceContext()
        self.__sub_service_context.sas_api = self.__sas_api
        self.__sub_service_context.sub_service_manager = self

        # All service
        self.__service_table = {}

        # Threads
        self.__service_threads = {}

        self.__period_service = []
        self.__thread_service = []
        self.__event_handler_service = []

    def init(self) -> bool:
        self.__plugin.refresh()
        modules = self.__plugin.all_modules()
        for module in modules:
            service_wrapper = PluginWrapper(self.__plugin, module)

            prob = service_wrapper.plugin_prob()
            if prob is None or 'plugin_id' not in prob or 'plugin_name' not in prob:
                continue

            capacities = service_wrapper.plugin_capacities()
            if capacities is None or not isinstance(capacities, (list, tuple)) or len(capacities) == 0:
                continue

            if 'thread' in capacities:
                self.__thread_service.append(service_wrapper)
            if 'polling' in capacities:
                self.__period_service.append(service_wrapper)
            if 'event_handler' in capacities:
                self.__event_handler_service.append(service_wrapper)
            self.__service_table[prob['plugin_id']] = service_wrapper

        return self.init_services() and self.startup_service() and self.activate_services()

    def init_services(self) -> bool:
        fail_service = []
        for identity, service_wrapper in self.__service_table.items():
            result = service_wrapper.init(sub_service_context=self.__sub_service_context)
            if not result:
                fail_service.append((identity, service_wrapper))
                prob = service_wrapper.plugin_prob()
                if isinstance(prob, dict):
                    print('Fail to init extension: ' + prob.get('plugin_id', 'NO ID'))
                else:
                    print('Fail to init extension: prob data error')
        self.__remove_service(fail_service)
        return True

    def startup_service(self) -> bool:
        fail_service = []
        for identity, service_wrapper in self.__service_table.items():
            result = service_wrapper.startup()
            if not result:
                fail_service.append((identity, service_wrapper))
        self.__remove_service(fail_service)
        return True

    def activate_services(self) -> bool:
        ret = True
        ret = ret and self.__register_event_handler_service()
        ret = ret and self.__run_thread_services()
        return ret

    def drive_service(self):
        self.__event_queue.polling(50)
        self.__poll_services()

    # ------------------------------------------ Event ------------------------------------------

    def post_event(self, event: Event):
        self.__event_queue.post_event(event)

    # -------------------------------------------------------------------------------------------

    def __register_event_handler_service(self) -> bool:
        for service_wrapper in self.__event_handler_service:
            self.__event_queue.add_event_handler(
                SubServiceManager.SubServiceEventWrapper(
                    str(uuid.uuid4()), service_wrapper.extension))
        return True

    def __run_thread_services(self) -> bool:
        for service_wrapper in self.__thread_service:
            extension_thread = SubServiceManager.SubServiceThreadWrapper(service_wrapper)
            service_wrapper.set_data('extension_thread', extension_thread)
            extension_thread.start()
        return True

    def __poll_services(self) -> bool:
        tick_ns = time.time() * 1000000
        if self.__prev_tick == 0:
            self.__prev_tick = tick_ns
        elapsed_ns = tick_ns - self.__prev_tick
        for service_wrapper in self.__period_service:
            service_wrapper.polling(elapsed_ns)
        self.__prev_tick = tick_ns
        return True

    def __remove_service(self, services: [PluginWrapper]):
        for identity, service_wrapper in services:
            if service_wrapper in self.__period_service:
                self.__period_service.remove(service_wrapper)
            if service_wrapper in self.__thread_service:
                self.__thread_service.remove(service_wrapper)
            if service_wrapper in self.__event_handler_service:
                self.__event_handler_service.remove(service_wrapper)
            del self.__service_table[identity]






