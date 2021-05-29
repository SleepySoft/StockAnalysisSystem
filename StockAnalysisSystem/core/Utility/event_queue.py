import time
import uuid
import datetime
import threading
import traceback
from collections import deque
from functools import partial


class Event:
    EVENT_MAIL = 'mail_event'               # Communication between sub-service
    EVENT_PUSH = 'push_event'               # Push message, push service can handle this kind of message
    EVENT_TIMER = 'timer_event'             # Period timer event
    EVENT_INVOKE = 'invoke_event'           # The event to invoke other sub-service feature
    EVENT_SCHEDULE = 'schedule_event'       # Triggered by system service scheduler
    EVENT_BROADCAST = 'broadcast_event'     # The event that can be received by all service

    def __init__(self, event_type: str, event_target: str, event_source: str = None):
        self.__id = str(uuid.uuid4())
        self.__event_type = event_type
        self.__event_target = event_target
        self.__event_source = event_source
        self.__event_data = {}
        self.__post_timestamp = datetime.datetime.now()
        self.__process_timestamp = datetime.datetime.now()

    def event_id(self) -> str:
        return self.__id

    def event_type(self) -> str:
        return self.__event_type

    def event_target(self) -> str or [str] or None:
        return self.__event_target

    def event_source(self) -> str:
        return self.__event_source

    # ---------------------------------------------------------------------

    def get_event_data(self) -> dict:
        return self.__event_data

    def set_event_data(self, _data: dict):
        self.__event_data = _data

    def update_event_data(self, _data: dict):
        self.__event_data.update(_data)

    def get_event_data_value(self, key: str, default_val: any = None) -> any:
        return self.__event_data.get(key, default_val)

    def set_event_data_value(self, key: str, val: any):
        self.__event_data[key] = val

    # ---------------------------------------------------------------------

    def get_post_timestamp(self) -> datetime.datetime:
        return self.__post_timestamp

    def get_process_timestamp(self) -> datetime.datetime:
        return self.__process_timestamp

    def update_post_timestamp(self):
        self.__post_timestamp = datetime.datetime.now()

    def update_process_timestamp(self):
        self.__process_timestamp = datetime.datetime.now()


# ----------------------------------------------------------------------------------------------------------------------

class EventInvoke(Event):
    def __init__(self, event_target: str):
        super(EventInvoke, self).__init__(Event.EVENT_INVOKE, event_target, '')

    def invoke(self, function: str, *args, **kwargs) -> bool:
        if not isinstance(function, str):
            return False
        self.set_event_data_value('invoke_function', function)
        self.set_event_data_value('invoke_args', args)
        self.set_event_data_value('invoke_kwargs', kwargs)
        return True

    def set_invoke_callback(self, callback):
        self.set_event_data_value('invoke_callback', callback)

    def get_invoke_function(self) -> str:
        return self.get_event_data_value('invoke_function')

    def get_invoke_parameters(self) -> (list, dict):
        return self.get_event_data_value('invoke_args'), \
               self.get_event_data_value('invoke_kwargs')

    def result(self) -> any:
        return self.get_event_data_value('invoke_result')

    def update_result(self, result: any):
        self.set_event_data_value('invoke_result', result)


# ----------------------------------------------------------------------------------------------------------------------

class EventHandler:
    def __init__(self):
        pass

    def identity(self) -> str:
        pass

    def handle_event(self, event: Event, sync: bool):
        pass


class EventQueue:
    def __init__(self):
        self.__event_handler = []
        self.__event_queue = deque(maxlen=1000)
        self.__lock = threading.Lock()

    def post_event(self, event: Event):
        with self.__lock:
            self.__event_queue.append(event)

    def insert_event(self, event: Event):
        with self.__lock:
            self.__event_queue.appendleft(event)

    def deliver_event(self, event: Event):
        self.__dispatch_event(event, True)

    def add_event_handler(self, event_handler: EventHandler):
        with self.__lock:
            self.__event_handler.append(event_handler)

    def polling(self, time_limit_ms: int) -> int:
        polling_start = datetime.datetime.now()
        while len(self.__event_queue) > 0:
            event = self.__event_queue.popleft()
            if self.__pre_process_event(event):
                self.__dispatch_event(event, False)
            if (datetime.datetime.now() - polling_start).microseconds >= time_limit_ms:
                break
        return len(self.__event_queue)

    # ------------------------------------------------------------------------------------------

    def __pre_process_event(self, event: Event):
        return True

    def __dispatch_event(self, event: Event, sync: bool):
        with self.__lock:
            event_handler_copy = self.__event_handler.copy()
        target = event.event_target()
        for handler in event_handler_copy:
            if target is None or len(target) == 0:
                handler.handle_event(event, sync)
            else:
                targets = list(target) if isinstance(target, (list, tuple, set)) else [str(target)]
                handler.handle_event(event, sync) if handler.identity() in targets else None


# ----------------------------------------------------------------------------------------------------------------------

class EventDispatcher(EventHandler):
    def __init__(self, in_private_thread: bool, name: str):
        if in_private_thread:
            self.__private_queue = EventQueue()
            self.__private_queue.add_event_handler(self)
            self.__private_thread = threading.Thread(target=self.__polling_thread)
        else:
            self.__private_queue = None
        self.__quit = False
        self.__lock = threading.Lock()
        self.__handler_name = name
        self.__invoke_mapping = {}
        self.__message_mapping = {}
        super(EventDispatcher, self).__init__()

    # def startup(self):
    #     if self.__private_thread is not None:
    #         self.__private_thread.start()

    def teardown(self):
        self.__quit = True
        if self.__private_thread is not None:
            self.__log('Event dispatcher %s thread teardown, joining...' % self.__handler_name)
            self.__private_thread.join()
            self.__log('Event dispatcher %s thread quit.' % self.__handler_name)

    # ----------------------------------------------------------------

    def dispatch_event(self, event: Event, sync: bool) -> bool:
        if self.__private_queue is not None and not sync:
            self.__private_queue.post_event(event)
            if not self.__private_thread.is_alive():
                self.__private_thread.start()
            return True
        else:
            return self.__handle_event(event)

    def register_invoke_handler(self, function: str, entry):
        """
        Register a function that will handle inter-service invoke.
        :param function: The name of function. This function can be invoked by this name.
        :param entry: The pointer of handle function.
                      The invoke params should follow this function's declaration.
        :return: None
        """
        with self.__lock:
            self.__invoke_mapping[function] = entry

    def register_message_handler(self, message_type: str, entry):
        """
        Register a function that will handle message event.
        :param message_type: The message type name that will be handled
        :param entry: The pointer of handle function.
                      The declaration of function should look like:
                        any_function_name(source: str, message_data: dict)
        :return: None
        """
        with self.__lock:
            self.__message_mapping[message_type] = entry

    # --------------- Override EventHandler Interface ---------------

    def identity(self) -> str:
        return self.__handler_name

    def handle_event(self, event: Event, sync: bool):
        self.__handle_event(event)

    # ---------------------------------------------------------------------------------------

    def __handle_event(self, event: Event) -> bool:
        if event.event_type() == Event.EVENT_INVOKE:
            return self.__handle_invoke(event)
        else:
            return self.__handle_message(event)

    def __handle_invoke(self, event: Event) -> bool:
        invoke_function = event.get_event_data_value('invoke_function')
        with self.__lock:
            entry = self.__invoke_mapping.get(invoke_function, None)
        if entry is None:
            return False
        args = event.get_event_data_value('invoke_args')
        kwargs = event.get_event_data_value('invoke_kwargs')
        try:
            result = entry(*args, **kwargs)
            event.set_event_data_value('invoke_result', result)
            invoke_callback = event.get_event_data_value('invoke_callback')
            if invoke_callback is not None:
                invoke_callback(result)
            return True
        except Exception as e:
            print('Invoke Fail: ' + str(e))
            print(traceback.format_exc())
            return False
        finally:
            pass

    def __handle_message(self, event: Event) -> bool:
        event_type = event.event_type()
        with self.__lock:
            entry = self.__message_mapping.get(event_type, None)
        if entry is None:
            return False
        try:
            entry(event.event_source(), event.get_event_data())
        except Exception as e:
            print('Message Fail: ' + str(e))
            print(traceback.format_exc())
            return False
        return True

    def __polling_thread(self):
        while not self.__quit:
            self.__private_queue.polling(1000)
            time.sleep(0.1)

    def __log(self, text: str):
        print(text)

