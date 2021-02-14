import psutil
import logging
import datetime
from apscheduler.schedulers.blocking import BaseScheduler, BlockingScheduler
import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.event_queue import Event
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext


logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.getLogger('apscheduler.executors').setLevel(logging.WARNING)
logging.getLogger('apscheduler.jobstores').setLevel(logging.WARNING)


# ----------------------------------------------------------------------------------------------------------------------

class SystemService:
    SCHEDULE_THREAD_DEFAULT = 'default_thread'
    SCHEDULE_THREAD_NEW = 'new_thread'

    SCHEDULE_EVERY_DAY = 'every_day'
    SCHEDULE_A_MARKET_TRADING_DAY = 'trading_day_a'

    class ScheduleDataBase:
        def __init__(self, scheduler: BaseScheduler, target: str, repeat: bool):
            self.__target = target
            self.__repeat = repeat
            self.__scheduler = scheduler

        def get_target(self) -> str:
            return self.__target

        def is_repeat(self) -> bool:
            return self.__repeat

        def get_scheduler(self) -> BaseScheduler:
            return self.__scheduler

        def schedule_handler(self):
            pass

        def re_schedule(self):
            pass

        def cancel_schedule(self):
            pass

    class TimerData(ScheduleDataBase):
        def __init__(self, scheduler: BaseScheduler, target: str, duration_ms: int, repeat: bool):
            self.__duration_ms = duration_ms
            super(SystemService.TimerData, self).__init__(scheduler, target, repeat)

        def schedule_handler(self):
            pass

        def re_schedule(self):
            self.get_scheduler().add_job(self.schedule_handler, 'interval', seconds=self.__duration_ms / 1000)

        def cancel_schedule(self):
            pass

    class ScheduleData(ScheduleDataBase):
        def __init__(self, scheduler: BaseScheduler, target: str, hour: int, minute: int, second: int,
                     repeat: bool, day_filter: str, run_thread: str):
            self.__hour = hour
            self.__minute = minute
            self.__second = second
            self.__day_filter = day_filter
            self.__run_thread = run_thread
            super(SystemService.ScheduleData, self).__init__(scheduler, target, repeat)

        def schedule_handler(self):
            pass

        def re_schedule(self):
            self.get_scheduler().add_job(self.schedule_handler, 'cron',
                                         hour=self.__hour, minute=self.__minute, second=self.__second)

        def cancel_schedule(self):
            pass

    def __init__(self, sub_service_context: SubServiceContext):
        self.__sub_service_context = sub_service_context
        self.__schedule = BlockingScheduler()
        self.__schedule_data = []
        self.__schedule.add_job(func=self.__watch_dog_task, trigger='interval', seconds=1, id='watch_dog_task')

    def run_forever(self):
        self.__schedule.start()
        logging.getLogger('apscheduler.executors.default').propagate = False
        logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)

    def register_sys_call(self):
        pass
        # self.__sas_api.register_sys_call('stock_memo_save',             self.__stock_memo.stock_memo_save,              group='stock_memo')

    # -----------------------------------------------------------------------

    def get_system_status(self) -> dict:
        mem = psutil.virtual_memory()
        netinfo = psutil.net_io_counters()
        return {
            'date_time': datetime.datetime.now(),
            'cpu_percent': psutil.cpu_percent(),
            'mem_percent': mem.percent,
            'bytes_sent': netinfo.bytes_sent,
            'bytes_recv': netinfo.bytes_recv
        }

    def get_system_status_str(self) -> str:
        system_status = self.get_system_status()
        return '%s  cpu: %s%%, mem: %s%%, bytes sent: %s, bytes recv: %s' % \
               (system_status['date_time'].strftime('%Y-%m-%d %H:%M:%S'),
                system_status['cpu_percent'], system_status['mem_percent'],
                system_status['bytes_sent'], system_status['bytes_recv'])

    # -----------------------------------------------------------------------

    def register_timer_event(self, target: str, duration_ms: int, repeat: bool):
        timer = SystemService.TimerData(self.__schedule, target, duration_ms, repeat)
        self.__schedule_data.append(timer)
        timer.re_schedule()

    def register_schedule_event(self, target: str, hour: int, minute: int, second: int, repeat=True,
                                day_filter: str = SCHEDULE_EVERY_DAY, run_thread: str = SCHEDULE_THREAD_DEFAULT):
        schedule = SystemService.ScheduleData(self.__schedule, target, hour, minute, second,
                                              repeat, day_filter, run_thread)
        self.__schedule_data.append(schedule)
        schedule.re_schedule()

    # -----------------------------------------------------------------------

    def __watch_dog_task(self):
        pass


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': '8e6e6025-c0c7-4577-b62a-dd26b925b874',
        'plugin_name': 'SystemService',
        'plugin_version': '0.0.0.1',
        'tags': ['System', 'Sleepy'],
    }


def plugin_adapt(service: str) -> bool:
    return service in ['8e6e6025-c0c7-4577-b62a-dd26b925b874']


def plugin_capacities() -> list:
    return [
        'api',            # Provides functions like sys call
        'thread',         # SubService manager will create a thread for this service
        'polling',        # polling() function will be invoked while event processing thread is free
        'event_handler'   # SubService can handle events that dispatch to it
    ]


# ----------------------------------------------------------------------------------------------------------------------

systemService: SystemService = None
subServiceContext: SubServiceContext = None


def init(sub_service_context: SubServiceContext) -> bool:
    try:
        global subServiceContext
        subServiceContext = sub_service_context

        global systemService
        systemService = SystemService(subServiceContext)
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
    global systemService
    systemService.run_forever()
    print('System service quit.')


def polling(interval_ns: int):
    pass


def event_handler(event: Event, **kwargs):
    pass




