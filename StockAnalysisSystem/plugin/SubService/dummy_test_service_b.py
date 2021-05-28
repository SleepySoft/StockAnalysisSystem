import time
import threading
import traceback

import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.digit_utility import to_int
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext
from StockAnalysisSystem.core.Utility.event_queue import Event, EventDispatcher


eventDispatcher: EventDispatcher = None
subServiceContext: SubServiceContext = None
SERVICE_ID = '23a49732-f3b0-43ec-9f5c-f8f64d6da649'


# ----------------------------------------------------------------------------------------------------------------------

def invoke_function_x(time_stamp: float, param1, param2) -> dict:
    ts = time.time()
    tid = threading.get_ident()
    print('function_x invoked at %s (delay %sms) in thread %s with param %s, %s' %
          (ts, (ts - time_stamp) * 1000, str(tid), str(param1), str(param2)))
    return {'thread_id': tid}


def invoke_function_y(time_stamp: float, param1, param2) -> dict:
    ts = time.time()
    tid = threading.get_ident()
    print('function_x invoked at %s (delay %sms) in thread %s with param %s, %s' %
          (ts, (ts - time_stamp) * 1000, str(tid), str(param1), str(param2)))
    return {'thread_id': tid}


def message_mail_event(source: str, message_data: dict):
    print('Get mail message from at B %s, data: %s' % (source, message_data))


def message_push_event(source: str, message_data: dict):
    print('Get push message from at B %s, data: %s' % (source, message_data))


def message_timer_event(source: str, message_data: dict):
    print('Get timer message at B from %s, data: %s' % (source, message_data))


def message_schedule_event(source: str, message_data: dict):
    print('Get schedule message at B from %s, data: %s' % (source, message_data))


def message_broadcast_event(source: str, message_data: dict):
    print('Get broadcast message at B from %s, data: %s' % (source, message_data))


def message_custom_event(source: str, message_data: dict):
    print('Get custom message at B from %s, data: %s' % (source, message_data))


def message_other_event(event: Event):
    print('Get un-handle event at B from %s, type: %s, data: %s' %
          (event.event_source(), event.event_type(), event.get_event_data()))


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': SERVICE_ID,
        'plugin_name': 'TestServiceB',
        'plugin_version': '0.0.0.1',
        'tags': ['Test', 'Sleepy'],
    }


def plugin_adapt(service: str) -> bool:
    return service == SERVICE_ID


def plugin_capacities() -> list:
    return [
        'polling',        # polling() function will be invoked while event processing thread is free
        'event_handler'   # SubService can handle events that dispatch to it
    ]


# ----------------------------------------------------------------------------------------------------------------------

def init(sub_service_context: SubServiceContext) -> bool:
    try:
        global eventDispatcher
        eventDispatcher = EventDispatcher(in_private_thread=False, name=SERVICE_ID)
        global subServiceContext
        subServiceContext = sub_service_context
    except Exception as e:
        import traceback
        print('Plugin-in init error: ' + str(e))
        print(traceback.format_exc())
    finally:
        pass
    return True


def startup() -> bool:
    eventDispatcher.register_invoke_handler('function_x', invoke_function_x)
    eventDispatcher.register_invoke_handler('function_y', invoke_function_y)
    eventDispatcher.register_message_handler(Event.EVENT_MAIL, message_mail_event)
    eventDispatcher.register_message_handler(Event.EVENT_PUSH, message_push_event)
    eventDispatcher.register_message_handler(Event.EVENT_TIMER, message_timer_event)
    eventDispatcher.register_message_handler(Event.EVENT_SCHEDULE, message_schedule_event)
    eventDispatcher.register_message_handler(Event.EVENT_BROADCAST, message_broadcast_event)
    eventDispatcher.register_message_handler('TestEventB', message_custom_event)
    return True


def teardown() -> bool:
    if eventDispatcher is not None:
        eventDispatcher.teardown()
    return True


def polling(interval_ns: int):
    pass


def event_handler(event: Event, sync: bool, **kwargs):
    if not eventDispatcher.dispatch_event(event, sync):
        message_other_event(event)

