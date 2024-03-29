import datetime

import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.Utility.event_queue import Event
from StockAnalysisSystem.core.DataHub.DataAgent import *
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext
from StockAnalysisSystem.core.DataHub.UniversalDataCenter import UniversalDataCenter


SERVICE_ID = 'ba561f10-2c6a-491e-8c0c-500b7b305a8a'


# ----------------------------------------------------------------------------------------------------------------------

class UpdateService:
    UPDATE_PERIOD_TABLE = {
        # URI                               (period, can slice, only trade day)
        'Market.TradeCalender':             (1,      False,     False),         # Must update first
        'Market.SecuritiesInfo':            (1,      False,     False),
        'Market.IndexInfo':                 (1,      False,     False),
        'Market.Enquiries':                 (1,      False,     False),
        'Market.NamingHistory':             (7,      False,     False),
        'Market.SecuritiesTags':            (7,      False,     False),

        'Finance.Audit':                    (7,      False,     False),
        'Finance.BalanceSheet':             (7,      True,      False),
        'Finance.IncomeStatement':          (7,      True,      False),
        'Finance.CashFlowStatement':        (7,      True,      False),

        'Finance.BusinessComposition':      (15,     True,      False),

        'Stockholder.Statistics':           (7,      False,     False),
        'Stockholder.PledgeStatus':         (7,      False,     False),
        'Stockholder.PledgeHistory':        (7,      False,     False),
        'Stockholder.ReductionIncrease':    (7,      False,     False),
        'Stockholder.Repurchase':           (7,      False,     False),
        'Stockholder.StockUnlock':          (7,      False,     False),

        'TradeData.Stock.Daily':            (1,      True,      True),
        'TradeData.Index.Daily':            (1,      False,     True),
        'Metrics.Stock.Daily':              (1,      True,      True),

    }

    # If the update is larger than the threshold. Just use serial update.
    UPDATE_THRESHOLD_DAY_DAILY = 60
    UPDATE_THRESHOLD_DAY_QUARTER = 365
    UPDATE_THRESHOLD_QUARTER_QUARTER = 4

    def __init__(self, sub_service_context: SubServiceContext):
        self.__sub_service_context = sub_service_context
        self.__progress = ProgressRate()
        self.__debug_info = True
        self.__nop = False

    def startup(self):
        # Delay 10s for startup check update
        # self.__sub_service_context.register_timer_event(target=SERVICE_ID, duration_ms=10000, repeat=False)

        # Daily check update at 23:00
        self.__sub_service_context.register_schedule_event(target=SERVICE_ID, hour=23, minute=0, second=0, period='daily')

    def handle_event(self, event: Event):
        if event.event_type() == Event.EVENT_SCHEDULE:
            self.check_update_all()
        elif event.event_type() == Event.EVENT_TIMER:
            self.check_update_all()

    # ---------------------------------------------------------------------------------------

    # Documents: Doc/Design.vsd - UpdateFlow

    def check_update_all(self):
        data_agents = self.__sub_service_context.sas_api.get_data_agents()
        data_agents_table = {agent.base_uri(): agent for agent in data_agents}
        for uri, properties in self.UPDATE_PERIOD_TABLE.items():
            data_agent = data_agents_table.get(uri, None)
            if data_agent is None:
                continue
            clock = Clock()
            print('> Check update for %s.' % uri)
            self.check_update_single(uri, properties, data_agent)
            print('< Check update for %s finished, time spending: %sms' % (uri, clock.elapsed_ms()))

    def check_update_single(self, uri: str, properties: tuple, data_agent: DataAgent) -> bool:
        update_period, can_slice, only_trade_day = properties
        ret, last_update_time, update_days = self.__calculate_update_range(uri)
        if not ret or last_update_time is None:
            return self.update_directly(uri)
        if update_days < update_period:
            return True
        data_duration = data_agent.data_duration()
        if data_duration in [DATA_DURATION_NONE, DATA_DURATION_AUTO, DATA_DURATION_FLOW]:
            self.update_directly(uri)
        elif data_duration == DATA_DURATION_DAILY:
            self.update_for_daily_data(uri, can_slice, only_trade_day, last_update_time, update_days)
        elif data_duration == DATA_DURATION_QUARTER:
            self.update_for_quarter_data(uri, can_slice, last_update_time, update_days)
        else:
            # DATA_DURATION_ANNUAL - Not support
            pass

    # -------------------------------------------------------------------

    def update_for_quarter_data(self, uri: str, can_slice: bool,
                                last_update_time: datetime.datetime, update_days: int) -> bool:
        if not can_slice or update_days > self.UPDATE_THRESHOLD_DAY_QUARTER:
            return self.update_directly(uri)

        quarters = []
        derive_time = now()
        while derive_time > last_update_time and len(quarters) < 6:
            prev_quarter = previous_quarter(derive_time)
            quarters.append(prev_quarter)
            derive_time = prev_quarter - datetime.timedelta(days=1)

        quarters.reverse()
        if len(quarters) > self.UPDATE_THRESHOLD_QUARTER_QUARTER or \
                not self.__slice_update_for_quarter(uri, quarters):
            return self.update_directly(uri)
        return True

    def update_directly(self, uri: str) -> bool:
        return self.__serial_update(uri)

    def update_for_daily_data(self, uri: str, can_slice: bool, only_trade_day,
                              last_update_time: datetime.datetime, update_days: int) -> bool:
        if not can_slice or update_days > self.UPDATE_THRESHOLD_DAY_DAILY:
            return self.update_directly(uri)
        if only_trade_day:
            trading_days = self.__sub_service_context.sas_if.sas_get_trading_days(last_update_time.date(), now().date())
            if not isinstance(trading_days, list):
                return False
            if len(trading_days) <= 1:
                return True

            # Think on this case: The update execute at morning, today's data are not exists.
            # But the last update time updates to today. So if we exclude the last update day, some data may be missing.

            # if trading_days[0] == last_update_time:
            #     trading_days.pop(0)
            update_days_list = [datetime.datetime.combine(
                d, datetime.time(hour=0, minute=0, second=0)) for d in trading_days]
        else:
            update_days_list = []
            derive_time = last_update_time
            while derive_time.date() <= now().date():
                update_days_list.append(derive_time)
                derive_time += datetime.timedelta(days=1)
        if not self.__slice_update_for_daily(uri, update_days_list):
            return self.update_directly(uri)
        return True

    # -------------------------------------------------------------------

    def __serial_update(self, uri: str) -> bool:
        if self.__debug_info:
            print('Serial update %s' % uri)
        if not self.__nop:
            ret = self.__sub_service_context.sas_api.data_utility().auto_update(uri, progress=self.__progress)
            return ret

    def __slice_update_for_quarter(self, uri: str, update_quarters: []):
        data_center: UniversalDataCenter = self.__sub_service_context.sas_api.data_center()
        for q in update_quarters:
            if self.__debug_info:
                print('Quarter slice update for %s - [%s]' % (uri, datetime2text(q)))
            if not self.__nop:
                ret = data_center.update_local_data(uri, time_serial=q)
                if not ret:
                    return False
        return True

    def __slice_update_for_daily(self, uri: str, update_days: []):
        data_center: UniversalDataCenter = self.__sub_service_context.sas_api.data_center()
        for d in update_days:
            if self.__debug_info:
                print('Daily slice update for %s - [%s]' % (uri, datetime2text(d)))
            if not self.__nop:
                ret = data_center.update_local_data(uri, time_serial=d)
                if not ret:
                    return False
        return True

    def __calculate_update_range(self, uri: str) -> (bool, datetime.datetime, int):
        last_update_time = self.__sub_service_context.sas_if.sas_get_last_update_time_from_update_table(uri.split('.'))
        last_update_date = to_date(last_update_time)

        if last_update_date is None:
            self.__sub_service_context.log('Error last update time format: ' + str(last_update_time))
            return False, None, 0

        date_delta = now().date() - last_update_date
        return True, last_update_time, date_delta.days

    # def __calculate_update_trade_data(self, last_update_time: datetime.datetime) -> [datetime.datetime]:
    #     # DEBUG: Test slice update
    #     if update_days > 1000:
    #         # More than 100 days, update per each
    #         ret = self.__update_daily_data_trade_per_each(uri)
    #         return ret
    #     else:
    #         # First try to update by slice
    #         ret = self.__update_daily_data_trade_by_slice(uri, last_update_time)
    #         if not ret:
    #             # If update by slice fail, update per each
    #             ret = self.__update_daily_data_trade_per_each(uri)
    #         return ret

    # ---------------------------------------------------------------------------------------

    # def __post_daily_update(self):
    #     """
    #     For avoiding update conflict. Post update to system queue.
    #     :return:
    #     """
    #     pass
    #
    # def __do_daily_update(self):
    #     self.__sub_service_context.log('%s: Do daily update.' %
    #                                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    #
    #     # DEBUG: Not update this for quick debug
    #     # self.__update_market_data()
    #
    #     self.__check_update_daily_trade_data('TradeData.Stock.Daily')
    #     self.__check_update_daily_trade_data('TradeData.Index.Daily')
    #     self.__check_update_daily_trade_data('Metrics.Stock.Daily')
    #
    # def __do_weekly_update(self):
    #     pass
    #
    # # --------------------------------------------------------------------------
    #
    # def __update_market_data(self):
    #     if not sasApi.update('Market.SecuritiesInfo'):
    #         raise Exception('Market.SecuritiesInfo update error.')
    #     if not sasApi.update('Market.IndexInfo'):
    #         raise Exception('Market.IndexInfo update error.')
    #     if not sasApi.update('Market.TradeCalender'):
    #         raise Exception('Market.TradeCalender update error.')
    #     self.__sub_service_context.log('Market data update complete.')

    # --------------------------------------------------------------------------

    # def __check_update_daily_trade_data(self, uri: str) -> bool:
    #     ret, last_update_time, update_days = \
    #         self.__estimate_daily_trade_data_update_range(uri)
    #
    #     if update_days == 0:
    #         # Newest, not need update.
    #         return True
    #     # DEBUG: Test slice update
    #     if update_days > 1000:
    #         # More than 100 days, update per each
    #         ret = self.__update_daily_data_trade_per_each(uri)
    #         return ret
    #     else:
    #         # First try to update by slice
    #         ret = self.__update_daily_data_trade_by_slice(uri, last_update_time)
    #         if not ret:
    #             # If update by slice fail, update per each
    #             ret = self.__update_daily_data_trade_per_each(uri)
    #         return ret

    # def __estimate_daily_trade_data_update_range(self, uri: str) -> (bool, datetime.datetime, int):
    #     last_update_time = self.__sub_service_context.sas_if.sas_get_last_update_time_from_update_table(uri.split('.'))
    #     last_update_date = to_date(last_update_time)
    #
    #     if last_update_date is None:
    #         self.__sub_service_context.log('Error last update time format: ' + str(last_update_time))
    #         return False, None, 0
    #
    #     date_delta = now().date() - last_update_date
    #     return True, last_update_time, date_delta.days
    #
    # def __update_daily_data_trade_by_slice(self, uri: str, since: datetime.datetime) -> bool:
    #     trading_days = self.__sub_service_context.sas_if.sas_get_trading_days(since, now().date())
    #     if not isinstance(trading_days, list):
    #         return False
    #     if len(trading_days) <= 1:
    #         return True
    #     trading_days.pop(0)
    #
    #     for trading_day in trading_days:
    #         ret = sasApi.update(uri, identity=None, time_serial=trading_day)
    #         if not ret:
    #             return False
    #     return True
    #
    # def __update_daily_data_trade_per_each(self, uri: str) -> bool:
    #     ret = sasApi.data_utility().auto_update(uri)
    #     return ret


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


def event_handler(event: Event, sync: bool, **kwargs):
    updateService.handle_event(event)




