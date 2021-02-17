import datetime

import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.event_queue import Event
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext


SERVICE_ID = '7129e9d2-4f53-4826-9161-c568ced52d02'

# ----------------------------------------------------------------------------------------------------------------------


class UpdateService:
    def __init__(self, sub_service_context: SubServiceContext):
        self.__sub_service_context = sub_service_context

    def startup(self):
        self.__sub_service_context.register_schedule_event(SERVICE_ID, 17, 0, 0)

    def handle_event(self, event: Event):
        if event.event_type() == Event.EVENT_SCHEDULE:
            self.__do_update()

    # ---------------------------------------------------------------------------------------

    def __do_update(self):
        self.__sub_service_context.log('%s: Do update.' %
                                       datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.__update_market_data()

    def __update_market_data(self):
        if not sasApi.update('Market.SecuritiesInfo'):
            raise Exception('Market.SecuritiesInfo update error.')
        if not sasApi.update('Market.IndexInfo'):
            raise Exception('Market.IndexInfo update error.')
        self.__sub_service_context.log('Market data update complete.')

    def update_daily_data_slice(self):
        pass

    def update_daily_data_each(self):
        pass


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': SERVICE_ID,
        'plugin_name': 'Update Service',
        'plugin_version': '0.0.0.1',
        'tags': ['Update', 'Sleepy'],
    }


def plugin_adapt(service: str) -> bool:
    return service == SERVICE_ID


def plugin_capacities() -> list:
    return [
        # 'api',            # Provides functions like sys call
        # 'thread',         # SubService manager will create a thread for this service
        # 'polling',        # polling() function will be invoked while event processing thread is free
        'event_handler'   # SubService can handle events that dispatch to it
    ]


# ----------------------------------------------------------------------------------------------------------------------

updateService: UpdateService = None
subServiceContext: SubServiceContext = None


def init(sub_service_context: SubServiceContext) -> bool:
    try:
        global subServiceContext
        subServiceContext = sub_service_context

        global updateService
        updateService = UpdateService(subServiceContext)
    except Exception as e:
        import traceback
        print('Plugin-in init error: ' + str(e))
        print(traceback.format_exc())
    finally:
        pass
    return True


def startup() -> bool:
    updateService.startup()
    return True


def event_handler(event: Event, **kwargs):
    updateService.handle_event(event)




