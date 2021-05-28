import traceback

import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.digit_utility import to_int
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext
from StockAnalysisSystem.core.Utility.event_queue import Event, EventDispatcher


once: bool = True
eventDispatcher: EventDispatcher = None
subServiceContext: SubServiceContext = None
SERVICE_ID = '23a49732-f3b0-43ec-9f5c-f8f64d6da649'


# ----------------------------------------------------------------------------------------------------------------------

def test_entry():
    pass


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

