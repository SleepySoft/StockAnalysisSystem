import threading
import time
import traceback

import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.digit_utility import to_int
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext
from StockAnalysisSystem.core.Utility.event_queue import Event, EventDispatcher


once: bool = True
eventDispatcher: EventDispatcher = None
subServiceContext: SubServiceContext = None
SERVICE_ID = 'f38cbc96-3b94-4cf2-bb36-fd9d4e656025'


# ----------------------------------------------------------------------------------------------------------------------

def test_analysis_result_brief_formatting():
    stock_identity = '000004.SZSE'

    df = subServiceContext.sas_api.data_center().query('Result.Analyzer', '000004.SZSE')
    if df is None or df.empty:
        return
    df = df.sort_values(by="period").drop_duplicates(subset=["analyzer"], keep="last")

    print(df)

    stock_name = subServiceContext.sas_api.data_utility().stock_identity_to_name('000004.SZSE')
    text = '%s [%s]' % (stock_name, stock_identity)

    if df.empty:
        return text + '无分析数据'

    strategy_name_dict = subServiceContext.sas_api.strategy_entry().strategy_name_dict()

    text_items = []
    for analyzer, period, brief, score in \
            zip(df['analyzer'], df['period'], df['brief'], df['score']):
        if score is not None and to_int(score, 999) <= 60:
            text_items.append('> %s: %s' % (strategy_name_dict.get(analyzer), brief))

    if len(text_items) == 0:
        text += '未发现风险项目'
    else:
        text += '风险项目\n----------------------------\n'
        text += '\n'.join(text_items)

    print(text)


TARGET_ID = '23a49732-f3b0-43ec-9f5c-f8f64d6da649'


def function_y_cb(result):
    print('function_y finished: ' + str(result))


def test_entry():
    result_x = subServiceContext.sub_service_manager.sync_invoke(
        '', 'function_x', time.time(), 'param1 from A', threading.get_ident())
    print('function_x returned: ' + str(result_x))

    event_y = subServiceContext.sub_service_manager.async_invoke(
        '23a49732-f3b0-43ec-9f5c-f8f64d6da649', 'function_y', function_y_cb,
        time.time(), 'param1 from A', threading.get_ident())
    print('Get function_y event: ' + str(event_y))

    subServiceContext.sub_service_manager.post_message(Event.EVENT_MAIL, TARGET_ID, SERVICE_ID, {'data': 'FromA'})
    subServiceContext.sub_service_manager.post_message(Event.EVENT_PUSH, TARGET_ID, SERVICE_ID, {'data': 'FromA'})
    subServiceContext.sub_service_manager.post_message(Event.EVENT_TIMER, TARGET_ID, SERVICE_ID, {'data': 'FromA'})
    subServiceContext.sub_service_manager.post_message(Event.EVENT_SCHEDULE, TARGET_ID, SERVICE_ID, {'data': 'FromA'})
    subServiceContext.sub_service_manager.post_message(Event.EVENT_BROADCAST, TARGET_ID, SERVICE_ID, {'data': 'FromA'})
    subServiceContext.sub_service_manager.post_message('TestEventB', TARGET_ID, SERVICE_ID, {'data': 'FromA'})
    subServiceContext.sub_service_manager.post_message('UnknownEvent', TARGET_ID, SERVICE_ID, {'data': 'FromA'})


# ----------------------------------------------------------------------------------------------------------------------

def invoke_function_a(time_stamp: float, param1, param2) -> dict:
    return {}


def invoke_function_b(time_stamp: float, param1, param2) -> dict:
    return {}


def message_mail_event(source: str, message_data: dict):
    print('Get mail message from at B %s, data: %s' % (source, message_data))


def message_push_event(source: str, message_data: dict):
    print('Get push message from at B %s, data: %s' % (source, message_data))


def message_timer_event(source: str, message_data: dict):
    print('Get timer message at A from %s, data: %s' % (source, message_data))


def message_schedule_event(source: str, message_data: dict):
    print('Get schedule message at A from %s, data: %s' % (source, message_data))


def message_broadcast_event(source: str, message_data: dict):
    print('Get broadcast message at A from %s, data: %s' % (source, message_data))


def message_custom_event(source: str, message_data: dict):
    print('Get custom message at A from %s, data: %s' % (source, message_data))


def message_other_event(event: Event):
    print('Get un-handle event at A from %s, type: %s, data: %s' % 
          (event.event_source(), event.event_type(), event.get_event_data()))


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': SERVICE_ID,
        'plugin_name': 'TestServiceA',
        'plugin_version': '0.0.0.1',
        'tags': ['Test', 'Sleepy'],
        'default_enable': False,
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
    eventDispatcher.register_invoke_handler('function_a', invoke_function_a)
    eventDispatcher.register_invoke_handler('function_b', invoke_function_b)
    eventDispatcher.register_message_handler(Event.EVENT_MAIL, message_mail_event)
    eventDispatcher.register_message_handler(Event.EVENT_PUSH, message_push_event)
    eventDispatcher.register_message_handler(Event.EVENT_TIMER, message_timer_event)
    eventDispatcher.register_message_handler(Event.EVENT_SCHEDULE, message_schedule_event)
    eventDispatcher.register_message_handler(Event.EVENT_BROADCAST, message_broadcast_event)
    eventDispatcher.register_message_handler('TestEventA', message_custom_event)
    return True


def teardown() -> bool:
    if eventDispatcher is not None:
        eventDispatcher.teardown()
    return True


def polling(interval_ns: int):
    global once
    if once:
        try:
            test_entry()
        except Exception as e:
            print("Test exception")
            print(e)
            print(traceback.format_exc())
        finally:
            once = False


def event_handler(event: Event, sync: bool, **kwargs):
    """
    Use this function to handle event. Includes timer and subscribed event.
    :param event: The event data
    :param sync: If true, it should not be handled in other thread
    :return:
    """
    print('Event')
    if not eventDispatcher.dispatch_event(event, sync):
        pass

