import datetime
import threading
from queue import Queue


class Event:
    TIMER_EVENT = 'timer_event'

    def __init__(self):
        self.__event_data = {}
        self.__post_timestamp = datetime.datetime.now()
        self.__process_timestamp = datetime.datetime.now()

    def event_class(self) -> str:
        return ''

    def event_target(self) -> str or [str] or None:
        return None

    # ---------------------------------------------------------------------

    def get_event_data(self, key: str) -> any:
        return self.__event_data.get(key, None)

    def set_event_data(self, key: str, val: any) -> any:
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
        self.__event_queue = Queue(1000)
        self.__lock = threading.Lock()

    def post_event(self, event: Event):
        self.__event_queue.put(event)

    def add_event_handler(self, event_handler: EventHandler):
        self.__event_handler.append(event_handler)

    def polling(self, time_limit_ms: int) -> int:
        polling_start = datetime.datetime.now()
        while not self.__event_queue.empty():
            event = self.__event_queue.get()
            if self.__pre_process_event(event):
                    self.__dispatch_event(event)
            if (datetime.datetime.now() - polling_start).microseconds >= time_limit_ms:
                break
        return self.__event_queue.qsize()

    def __pre_process_event(self, event: Event):
        pass

    def __dispatch_event(self, event: Event):
        with self.__lock:
            event_handler_copy = self.__event_handler.copy()
        for handler in event_handler_copy:
            target = event.event_target()
            if target is None or len(target) == 0:
                handler.handle_event(event)
            else:
                targets = list(target) if isinstance(target, (list, tuple, set)) else [str(target)]
                if handler.identity in targets:
                    handler.handle_event(event)


