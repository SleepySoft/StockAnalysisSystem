import uuid
import datetime
import threading
from collections import deque


class Event:
    EVENT_ACK = 'ack_event'                 # The reply event of EVENT_INVOKE
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

    def update_event_data(self, k: str, v: any):
        self.__event_data[k] = v

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

class EventAck(Event):
    def __init__(self, event_source: str, ack_event: Event, invoke_result: any):
        self.update_event_data('ack_event', ack_event)
        self.update_event_data('invoke_result', invoke_result)
        super(EventAck, self).__init__(Event.EVENT_ACK, ack_event.event_source(), event_source)

    def get_ack_event(self) -> Event:
        return self.get_event_data().get('ack_event')

    def get_invoke_result(self) -> any:
        return self.get_event_data().get('invoke_result')


class EventInvoke(Event):
    def __init__(self, event_target: str, event_source: str, invoke_function: str, **kwargs):
        self.set_event_data('invoke_function', invoke_function)
        self.set_event_data('invoke_parameters', kwargs)
        super(EventInvoke, self).__init__(Event.EVENT_INVOKE, event_target, event_source)

    def get_invoke_function(self) -> str:
        return self.get_event_data().get('invoke_function')

    def get_invoke_parameters(self) -> dict:
        return self.get_event_data().get('invoke_parameters')


# ----------------------------------------------------------------------------------------------------------------------

class EventHandler:
    def __init__(self):
        pass

    def identity(self) -> str:
        pass

    def handle_event(self, event: Event):
        pass


class EventQueue:
    def __init__(self):
        self.__event_handler = []
        self.__event_queue = deque(maxlen=1000)
        self.__lock = threading.Lock()

    def post_event(self, event: Event):
        self.__event_queue.append(event)

    def insert_event(self, event: Event):
        self.__event_queue.appendleft(event)

    def deliver_event(self, event: Event):
        self.__dispatch_event(event)

    def add_event_handler(self, event_handler: EventHandler):
        self.__event_handler.append(event_handler)

    def polling(self, time_limit_ms: int) -> int:
        polling_start = datetime.datetime.now()
        while len(self.__event_queue) > 0:
            event = self.__event_queue.popleft()
            if self.__pre_process_event(event):
                self.__dispatch_event(event)
            if (datetime.datetime.now() - polling_start).microseconds >= time_limit_ms:
                break
        return len(self.__event_queue)

    def __pre_process_event(self, event: Event):
        return True

    def __dispatch_event(self, event: Event):
        with self.__lock:
            event_handler_copy = self.__event_handler.copy()
        for handler in event_handler_copy:
            target = event.event_target()
            if target is None or len(target) == 0:
                handler.handle_event(event)
            else:
                targets = list(target) if isinstance(target, (list, tuple, set)) else [str(target)]
                if handler.identity() in targets:
                    handler.handle_event(event)


