import time
import threading
import collections
from concurrent.futures.thread import ThreadPoolExecutor

import psutil
import logging
import datetime
from apscheduler.schedulers.blocking import BaseScheduler, BlockingScheduler
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.Utility.event_queue import Event
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext


logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.getLogger('apscheduler.executors').setLevel(logging.WARNING)
logging.getLogger('apscheduler.jobstores').setLevel(logging.WARNING)

# ----------------------------------------------------------------------------------------------------------------------

subServiceContext: SubServiceContext = None
SERVICE_ID = '8e6e6025-c0c7-4577-b62a-dd26b925b874'


# ----------------------------------------------------------------------------------------------------------------------

class SystemService:

    SCHEDULE_THREAD_NEW = 'new_thread'
    SCHEDULE_THREAD_DEFAULT = 'default_thread'

    class ScheduleDataBase:
        def __init__(self, scheduler: BaseScheduler, target: str, repeat: bool, extra: dict):
            self.__extra = extra
            self.__target = target
            self.__repeat = repeat
            self.__scheduler = scheduler

        def get_target(self) -> str:
            return self.__target

        def is_repeat(self) -> bool:
            return self.__repeat

        def get_scheduler(self) -> BaseScheduler:
            return self.__scheduler

        def get_extra_data(self) -> dict:
            return self.__extra

        def schedule_handler(self):
            pass

        def re_schedule(self):
            pass

        def cancel_schedule(self):
            pass

    class TimerData(ScheduleDataBase):
        def __init__(self, scheduler: BaseScheduler, target: str, duration_ms: int, repeat: bool, **kwargs):
            self.__duration_ms = duration_ms
            super(SystemService.TimerData, self).__init__(scheduler, target, repeat, kwargs)

        def schedule_handler(self):
            timer_event = Event(Event.EVENT_TIMER, self.get_target())
            timer_event.set_event_data(self.get_extra_data())
            subServiceContext.sub_service_manager.insert_event(timer_event)
            # if self.is_repeat():
            #     self.re_schedule()

        def re_schedule(self):
            self.get_scheduler().add_job(self.schedule_handler, 'interval', seconds=self.__duration_ms / 1000)

        def cancel_schedule(self):
            pass

    class ScheduleData(ScheduleDataBase):
        THREAD_POOL = ThreadPoolExecutor(max_workers=5)

        def __init__(self, scheduler: BaseScheduler, target: str, hour: int, minute: int, second: int,
                     repeat: bool, run_thread: str, **kwargs):
            self.__hour = hour
            self.__minute = minute
            self.__second = second
            self.__run_thread = run_thread
            self.__job = None
            super(SystemService.ScheduleData, self).__init__(scheduler, target, repeat, kwargs)

        def schedule_handler(self):
            schedule_event = Event(Event.EVENT_SCHEDULE, self.get_target())
            schedule_event.set_event_data(self.get_extra_data())

            if self.__run_thread:
                # If run_thread is set, deliver this event by the thread of thread pool
                # TODO: How to keep the futurn for further trace?
                future = self.THREAD_POOL.submit(self.__execute_schedule_job, schedule_event)
            else:
                # Otherwise just post it to the event queue
                subServiceContext.sub_service_manager.insert_event(schedule_event)
            # if self.is_repeat():
            #     self.re_schedule()

        def re_schedule(self):
            self.__job = self.get_scheduler().add_job(self.schedule_handler, 'cron',
                                                      hour=self.__hour, minute=self.__minute, second=self.__second)

        def cancel_schedule(self):
            self.get_scheduler()

        def __execute_schedule_job(self, schedule_event: Event):
            subServiceContext.sub_service_manager.deliver_event(schedule_event)

    WATCH_DOG_TIMER_INTERVAL = 1.0          # 1s

    def __init__(self, sub_service_context: SubServiceContext):
        self.__sub_service_context = sub_service_context
        self.__scheduler = BlockingScheduler()
        self.__schedule_data = []
        self.__scheduler.add_job(func=self.__watch_dog_task, trigger='interval', seconds=1, id='watch_dog_task')

        # For service polling thread monitoring
        self.__prev_run_cycles = 0
        # For timer monitoring
        # Ring buffer, see: https://stackoverflow.com/a/4151368
        self.__timer_gap_buffer = collections.deque(maxlen=10)
        self.__timer_event_expect_time = 0
        # For schedule monitoring
        self.__schedule_duration_buffer = collections.deque(maxlen=10)
        self.__schedule_event_expect_time = 0

    def run_forever(self):
        self.__scheduler.start()
        print('Scheduler quit.')

    def handle_event(self, event: Event):
        if event.event_type() == Event.EVENT_TIMER:
            # Record the gap and update the next expect time.
            now_ts = time.time()
            time_gap = now_ts - self.__timer_event_expect_time
            self.__timer_gap_buffer.append(time_gap)
            self.__timer_event_expect_time = now_ts + SystemService.WATCH_DOG_TIMER_INTERVAL
        elif event.event_type() == Event.EVENT_SCHEDULE:
            print('Receive schedule event: ' + datetime2text(now()))

    def register_sys_call(self):
        subServiceContext.sas_api.register_sys_call('get_system_status',        self.get_system_status,         group='system_service')
        subServiceContext.sas_api.register_sys_call('get_system_status_str',    self.get_system_status_str,     group='system_service')

        subServiceContext.sas_api.register_sys_call('register_timer_event',     self.register_timer_event,      group='system_service')
        subServiceContext.sas_api.register_sys_call('register_schedule_event',  self.register_schedule_event,   group='system_service')

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

    def register_timer_event(self, target: str, duration_ms: int, repeat: bool = True, **kwargs):
        timer = SystemService.TimerData(self.__scheduler, target, duration_ms, repeat, **kwargs)
        self.__schedule_data.append(timer)
        timer.re_schedule()

    def register_schedule_event(self, target: str, hour: int, minute: int, second: int, repeat=True,
                                run_thread: str = SCHEDULE_THREAD_DEFAULT, **kwargs):
        schedule = SystemService.ScheduleData(self.__scheduler, target, hour, minute, second,
                                              repeat, run_thread, **kwargs)
        self.__schedule_data.append(schedule)
        schedule.re_schedule()

    # ---------------------------- Sytem Monitor ----------------------------

    def __watch_dog_task(self):
        self.__check_system_status()
        self.__check_service_thread()
        self.__check_timer_event()
        self.__check_schedule_event()

    def __check_system_status(self):
        pass

    def __check_service_thread(self):
        last_run_time = subServiceContext.sub_service_manager.get_last_run_time()
        last_run_cycles = subServiceContext.sub_service_manager.get_running_cycles()

        if self.__prev_run_cycles != 0:
            if time.time() - last_run_time > 1000:
                print('Warning: Service timeout.')
            if last_run_cycles - self.__prev_run_cycles < 5:
                print('Warning: Service runs slow.')

        self.__prev_run_cycles = last_run_cycles

    def __check_timer_event(self):
        if self.__timer_event_expect_time == 0:
            # The first time, register a repeat timer
            self.__timer_event_expect_time = time.time() + SystemService.WATCH_DOG_TIMER_INTERVAL
            self.__sub_service_context.sas_if.register_timer_event(
                SERVICE_ID, SystemService.WATCH_DOG_TIMER_INTERVAL * 1000, True)
        elif time.time() - self.__timer_event_expect_time > 5.0:
            # If the expect time hasn't being update for 5s, the timer thread may be blocked.
            print('Timer seems being blocked.')
        else:
            if len(self.__timer_gap_buffer) > 0:
                max_gap = max(self.__timer_gap_buffer)
                if max_gap > SystemService.WATCH_DOG_TIMER_INTERVAL * 0.1:
                    pass
                    # print('Max timer gap > 10%.')

    def __check_schedule_event(self):
        if self.__schedule_event_expect_time == 0:
            self.__sub_service_context.sas_if.register_schedule_event(SERVICE_ID, 8, 0, 0, True)
            self.__schedule_event_expect_time = time.time()


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': SERVICE_ID,
        'plugin_name': 'SystemService',
        'plugin_version': '0.0.0.1',
        'tags': ['System', 'Sleepy'],
    }


def plugin_adapt(service: str) -> bool:
    return service == SERVICE_ID


def plugin_capacities() -> list:
    return [
        'api',            # Provides functions like sys call
        'thread',         # SubService manager will create a thread for this service
        'polling',        # polling() function will be invoked while event processing thread is free
        'event_handler'   # SubService can handle events that dispatch to it
    ]


# ----------------------------------------------------------------------------------------------------------------------

systemService: SystemService = None


def init(sub_service_context: SubServiceContext) -> bool:
    try:
        global subServiceContext
        subServiceContext = sub_service_context

        global systemService
        systemService = SystemService(subServiceContext)
        systemService.register_sys_call()
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
    systemService.run_forever()
    print('System service quit.')


def polling(interval_ns: int):
    pass


def event_handler(event: Event, sync: bool, **kwargs):
    systemService.handle_event(event)




