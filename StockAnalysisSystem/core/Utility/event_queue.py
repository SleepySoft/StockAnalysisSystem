import datetime
import threading
from collections import deque


class Event:
    EVENT_MAIL = 'mail_event'
    EVENT_PUSH = 'push_event'
    EVENT_TIMER = 'timer_event'
    EVENT_INVOKE = 'invoke_event'
    EVENT_SCHEDULE = 'schedule_event'
    EVENT_BROADCAST = 'broadcast_event'

    def __init__(self, event_type: str, event_target: str, event_sign: str = ''):
        self.__event_type = event_type
        self.__event_target = event_target
        self.__event_sign = event_sign
        self.__event_data = {}
        self.__post_timestamp = datetime.datetime.now()
        self.__process_timestamp = datetime.datetime.now()

    def event_type(self) -> str:
        return self.__event_type

    def event_target(self) -> str or [str] or None:
        return self.__event_target

    def event_sign(self) -> str:
        return self.__event_sign

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


