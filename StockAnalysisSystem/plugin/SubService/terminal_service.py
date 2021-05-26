import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext
from StockAnalysisSystem.core.Utility.event_queue import Event, EventInvoke, EventAck
from StockAnalysisSystem.core.Utility.relative_import import RelativeImport

with RelativeImport(__file__):
    from WebServiceProvider.service_provider import ServiceProvider


SERVICE_ID = '0ea2afb5-3350-46e8-af1b-2e7ff246a1ff'


# ----------------------------------------------------------------------------------------------------------------------

"""
Support event:
    Event type: Event.EVENT_INVOKE
    Event 
"""


class TerminalService:
    def __init__(self):
        self.__service_provider: SubServiceContext = None
        self.__subService_context: SubServiceContext = None

    def init(self, sub_service_context: SubServiceContext):
        self.__service_provider = ServiceProvider()
        self.__subService_context = sub_service_context
        self.__service_provider.check_init(sub_service_context.sas_if,
                                           sub_service_context.sas_api)
        return self.__service_provider.is_inited()

    def handle_event(self, event: Event, **kwargs):
        if event.event_type() == Event.EVENT_INVOKE:
            invoke_function = event.get_event_data_value('invoke_function')
            if invoke_function == 'interact':
                self.__handle_interact(event, **kwargs)

    def __handle_interact(self, event: Event, **kwargs):
            invoke_parameters = event.get_event_data_value('invoke_parameters')
            self.__service_provider.interact()

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

terminalService = TerminalService()


def init(sub_service_context: SubServiceContext) -> bool:
    try:
        return terminalService.init(sub_service_context)
    except Exception as e:
        import traceback
        print('Plugin-in init error: ' + str(e))
        print(traceback.format_exc())
    finally:
        pass
    return True


def startup() -> bool:
    return True


# def thread(context: dict):
#     pass


# def polling(interval_ns: int):
#     pass


def event_handler(event: Event, **kwargs):
    terminalService.handle_event(event, **kwargs)




