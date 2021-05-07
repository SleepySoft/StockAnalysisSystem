import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext
from StockAnalysisSystem.core.Utility.event_queue import Event, EventInvoke, EventAck


SERVICE_ID = '0ea2afb5-3350-46e8-af1b-2e7ff246a1ff'


# ----------------------------------------------------------------------------------------------------------------------

class TerminalService:
    def __init__(self):
        pass

# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': SERVICE_ID,
        'plugin_name': 'terminal_service',
        'plugin_version': '0.0.0.1',
        'tags': ['Terminal', 'Sleepy'],
    }


def plugin_adapt(service: str) -> bool:
    return service == SERVICE_ID


def plugin_capacities() -> list:
    return [
        'api',            # Provides functions like sys call
        # 'thread',         # SubService manager will create a thread for this service
        # 'polling',        # polling() function will be invoked while event processing thread is free
        'event_handler'   # SubService can handle events that dispatch to it
    ]


# ----------------------------------------------------------------------------------------------------------------------

subServiceContext: SubServiceContext = None


def init(sub_service_context: SubServiceContext) -> bool:
    try:
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


def thread(context: dict):
    pass


def polling(interval_ns: int):
    pass


def event_handler(event: Event, **kwargs):
    pass




