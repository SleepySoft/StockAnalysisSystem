import datetime

import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.Utility.event_queue import Event
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext


SERVICE_ID = '7129e9d2-4f53-4826-9161-c568ced52d02'

# ----------------------------------------------------------------------------------------------------------------------


class UpdateService:
    def __init__(self, sub_service_context: SubServiceContext):
        self.__sub_service_context = sub_service_context

    def startup(self):
        # DEBUG: Debug event
        # event = Event('update_service_test', SERVICE_ID)
        # event.update_event_data('update_service_test_flag', 'daily')
        # self.__sub_service_context.sub_service_manager.post_event(event)

        self.__sub_service_context.register_schedule_event(SERVICE_ID, 17, 0, 0, period='daily')
        self.__sub_service_context.register_schedule_event(SERVICE_ID, 21, 0, 0, period='weekly')

    def handle_event(self, event: Event):
        if event.event_type() == Event.EVENT_SCHEDULE:
            if event.get_event_data().get('period', '') == 'daily':
                self.__do_daily_update()
            elif event.get_event_data().get('period', '') == 'weekly':
                # Friday
                if now_week_days() == 6:
                    self.__do_weekly_update()
        elif event.event_type() == 'update_service_test':
            if event.get_event_data().get('update_service_test_flag', '') == 'daily':
                self.__do_daily_update()

    # ---------------------------------------------------------------------------------------

    def __post_daily_update(self):
        """
        For avoiding update conflict. Post update to system queue.
        :return:
        """
        pass

    def __do_daily_update(self):
        self.__sub_service_context.log('%s: Do daily update.' %
                                       datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # DEBUG: Not update this for quick debug
        # self.__update_market_data()

        self.__check_update_daily_trade_data('TradeData.Stock.Daily')
        self.__check_update_daily_trade_data('TradeData.Index.Daily')
        self.__check_update_daily_trade_data('Metrics.Stock.Daily')

    def __do_weekly_update(self):
        pass

    # --------------------------------------------------------------------------

    def __update_market_data(self):
        if not sasApi.update('Market.SecuritiesInfo'):
            raise Exception('Market.SecuritiesInfo update error.')
        if not sasApi.update('Market.IndexInfo'):
            raise Exception('Market.IndexInfo update error.')
        if not sasApi.update('Market.TradeCalender'):
            raise Exception('Market.TradeCalender update error.')
        self.__sub_service_context.log('Market data update complete.')

    # --------------------------------------------------------------------------

    def __check_update_daily_trade_data(self, uri: str) -> bool:
        ret, last_update_time, update_days = \
            self.__estimate_daily_trade_data_update_range(uri)

        if update_days == 0:
            # Newest, not need update.
            return True
        # DEBUG: Test slice update
        if update_days > 1000:
            # More than 100 days, update per each
            ret = self.__update_daily_data_trade_per_each(uri)
            return ret
        else:
            # First try to update by slice
            ret = self.__update_daily_data_trade_by_slice(uri, last_update_time)
            if not ret:
                # If update by slice fail, update per each
                ret = self.__update_daily_data_trade_per_each(uri)
            return ret

    def __estimate_daily_trade_data_update_range(self, uri: str) -> (bool, datetime.datetime, int):
        last_update_time = self.__sub_service_context.sas_if.sas_get_last_update_time_from_update_table(uri.split('.'))
        last_update_date = to_date(last_update_time)

        if last_update_date is None:
            self.__sub_service_context.log('Error last update time format: ' + str(last_update_time))
            return False, None, 0

        date_delta = now().date() - last_update_date
        return True, last_update_time, date_delta.days

    def __update_daily_data_trade_by_slice(self, uri: str, since: datetime.datetime) -> bool:
        trading_days = self.__sub_service_context.sas_if.sas_get_trading_days(since, now().date())
        if not isinstance(trading_days, list):
            return False
        if len(trading_days) <= 1:
            return True
        trading_days.pop(0)

        for trading_day in trading_days:
            ret = sasApi.update(uri, identity=None, time_serial=trading_day)
            if not ret:
                return False
        return True

    def __update_daily_data_trade_per_each(self, uri: str) -> bool:
        ret = sasApi.data_utility().auto_update(uri)
        return ret


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




