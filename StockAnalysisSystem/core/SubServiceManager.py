import time
import uuid
from functools import partial
from threading import Thread

import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.event_queue import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.Utility.plugin_manager import *
from StockAnalysisSystem.interface.interface import SasInterface


class SubServiceContext:
    def __init__(self):
        self.sas_if: SasInterface = None
        self.sas_api: sasApi = None
        self.sub_service_manager = None
        self.extra_data = {}

    def log(self, text: str):
        print(text)

    def __getattr__(self, attr):
        return partial(self.__service_call, attr)

    def __service_call(self, api, *args, **kwargs) -> any:
        try:
            return self.sas_api.sys_call(api, *args, **kwargs)
        except Exception as e:
            self.log('Sub Service call error: ' + str(e))
            self.log(traceback.format_exc())
            return None
        finally:
            pass


class SubServiceManager:
    class SubServiceThreadWrapper(Thread):
        def __init__(self, extension: PluginWrapper):
            super(SubServiceManager.SubServiceThreadWrapper, self).__init__()
            self.__context = {'quit_flag': False}
            self.__extension = extension

        def run(self):
            ret = self.__extension.thread(context=self.__context)
            print('Sub Service thread exit, return = ' + str(ret))

        def teardown(self):
            self.__context['quit_flag'] = True

    class SubServiceEventWrapper(EventHandler):
        def __init__(self, extension: PluginWrapper):
            self.__extension = extension
            prob = extension.plugin_prob()
            self.__identity = prob['plugin_id']
            super(SubServiceManager.SubServiceEventWrapper, self).__init__()

        def identity(self) -> str:
            return self.__identity

        def handle_event(self, event: Event, sync: bool):
            self.__extension.event_handler(event=event, sync=sync)

    def __init__(self, sas_api: sasApi, plugin: PluginManager):
        self.__sas_api = sas_api
        self.__plugin = plugin

        self.__prev_tick = 0
        self.__event_queue = EventQueue()

        from StockAnalysisSystem.interface.interface_local import LocalInterface
        self.__sub_service_context = SubServiceContext()
        self.__sub_service_context.sas_if = LocalInterface()
        self.__sub_service_context.sas_api = self.__sas_api
        self.__sub_service_context.sub_service_manager = self

        # All service
        self.__service_table = {}

        # Service reference
        self.__period_service = []
        self.__thread_service = []
        self.__event_handler_service = []

        # Threads
        self.__quit = False
        self.__lock = threading.Lock()
        self.__service_thread = None

        # SubService Threads
        self.__sub_service_threads = []

        # Statistics
        self.__last_run_time = 0
        self.__running_cycles = 0

    # --------------------------------------- Init & Startup ---------------------------------------

    def init(self) -> bool:
        config = self.__sas_api.config()
        enable_service = config.get('ENABLE_SERVICES', [])
        disable_service = config.get('DISABLE_SERVICES', [])
        enable_service_id = [s[0] for s in enable_service]
        disable_service_id = [s[0] for s in disable_service]

        self.__plugin.refresh()
        modules = self.__plugin.all_modules()
        for module in modules:
            service_wrapper = PluginWrapper(self.__plugin, module)

            prob = service_wrapper.plugin_prob()
            if prob is None or 'plugin_id' not in prob or 'plugin_name' not in prob:
                continue

            plugin_id = prob['plugin_id']

            # If "default_enable" of service prob is False, it should be enabled by "ENABLE_SERVICES" in json
            if not prob.get('default_enable', True) and plugin_id not in enable_service_id:
                continue

            if plugin_id in disable_service_id:
                self.__log('Service %s disabled' % prob['plugin_name'])
                continue

            service_wrapper.set_data('plugin_id', plugin_id)
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

        return True

    def startup(self) -> bool:
        return self.init_services() and self.startup_service() and self.activate_services()

    def teardown(self):
        self.__quit = False
        if self.__service_thread is not None:
            self.__log('SebServiceManager Teardown, joining service thread...')
            self.__service_thread.join()
            self.__log('SebServiceManager Teardown, service thread quit.')
        for _id, sub_service in self.__service_table.items():
            sub_service.teardown()

    def init_services(self) -> bool:
        fail_service = []
        for identity, service_wrapper in self.__service_table.items():
            result = service_wrapper.init(sub_service_context=self.__sub_service_context)
            if not result:
                fail_service.append((identity, service_wrapper))
                prob = service_wrapper.plugin_prob()
                if isinstance(prob, dict):
                    self.__log('Fail to init extension: ' + prob.get('plugin_id', 'NO ID'))
                else:
                    self.__log('Fail to init extension: prob data error')
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

    def teardown_service(self):
        for service_wrapper in self.__thread_service:
            plugin_id = service_wrapper.get_data('plugin_id')
            extension_thread: SubServiceManager.SubServiceThreadWrapper = \
                service_wrapper.get_data('extension_thread')
            self.__log('Sub service %s thread teardown, joining...' % plugin_id)
            extension_thread.teardown()
            self.__log('Sub service %s thread quit.' % plugin_id)

    # ---------------------------------------- Functions ----------------------------------------

    def run_service(self):
        self.__service_thread = threading.Thread(target=self.run_forever)
        self.__service_thread.start()

    def run_forever(self):
        while not self.__quit:
            self.poll_service()
            time.sleep(0.05)

    def poll_service(self):
        with self.__lock:
            self.__last_run_time = int(time.time() * 1000)
            self.__running_cycles += 1
        self.__event_queue.polling(50)
        self.__poll_services()

    def get_last_run_time(self) -> int:
        with self.__lock:
            return self.__last_run_time

    def get_running_cycles(self) -> int:
        with self.__lock:
            return self.__running_cycles

    # --------------------------------------- Transaction ---------------------------------------

    def sync_invoke(self, target: str or [str] or None, function: str, *args, **kwargs) -> any:
        """
        Invoke function sync. The function will be invoked directly in the same thread.
        :param target: The id of target service. None or empty string to invoke the first match service.
        :param function: The function name that you will invoke.
        :param args: The list parameters
        :param kwargs: The named parameters
        :return: The invoke result
        """
        event = EventInvoke(target)
        event.invoke(function, *args, **kwargs)
        self.__event_queue.deliver_event(event)
        return event.result()

    def async_invoke(self, target: str or [str] or None, function: str,
                     invoke_callback, *args, **kwargs) -> EventInvoke or None:
        """
        Invoke function async. The function will return immediately.
        :param target: The id of target service. None or empty string to invoke the first match service.
        :param function: The function name that you will invoke.
        :param invoke_callback: The function will be called after the invoke finished. None if you don't want callback.
                                The callback function should have one parameter named 'result' to retrieve the invoke result.
                                If you want to pass more data or context into this callback, you can use partial instead.
                                The callback thread is the invoke thread which is uncertain.
        :param args: The list parameters
        :param kwargs: The named parameters
        :return: Instance of EventInvoke or None if error occurs.
        """
        event = EventInvoke(target)
        if event.invoke(function, *args, **kwargs):
            event.set_invoke_callback(invoke_callback)
            self.__event_queue.post_event(event)
            return event
        else:
            return None

    def post_message(self, message_type: str, receiver: str or [str] or None, sender: str, _data: dict, **kwargs):
        """
        Post a message to other service.
        :param message_type: Message type as string. The Event class defines some standard message type.
        :param receiver: The id of target service
        :param sender: The id of sender service
        :param _data: The message data as dict
        :param kwargs: Other parameters, will be combined with _data
        :return: None
        """
        event = Event(message_type, receiver, sender)
        event.set_event_data(_data)
        event.update_event_data(kwargs)
        self.__event_queue.post_event(event)

    # ------------------------------------------ Event ------------------------------------------

    def post_event(self, event: Event):
        self.__event_queue.post_event(event)

    def insert_event(self, event: Event):
        self.__event_queue.insert_event(event)

    def deliver_event(self, event: Event):
        self.__event_queue.deliver_event(event)

    # ----------------------------------------- private -----------------------------------------

    def __poll_services(self) -> bool:
        tick_ns = time.time() * 1000000
        if self.__prev_tick == 0:
            self.__prev_tick = tick_ns
        elapsed_ns = tick_ns - self.__prev_tick
        for service_wrapper in self.__period_service:
            service_wrapper.polling(interval_ns=elapsed_ns)
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

    def __register_event_handler_service(self) -> bool:
        for service_wrapper in self.__event_handler_service:
            self.__event_queue.add_event_handler(
                SubServiceManager.SubServiceEventWrapper(service_wrapper))
        return True

    def __run_thread_services(self) -> bool:
        for service_wrapper in self.__thread_service:
            extension_thread = SubServiceManager.SubServiceThreadWrapper(service_wrapper)
            service_wrapper.set_data('extension_thread', extension_thread)
            extension_thread.start()
            self.__sub_service_threads.append(extension_thread)
        return True

    def __log(self, text: str):
        print(text)





