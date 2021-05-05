from wxpy import *
import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.event_queue import Event
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext

SERVICE_ID = '12d59df4-c218-45af-9a3e-a0b99526c291'


# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': SERVICE_ID,
        'plugin_name': 'wechat_robot',
        'plugin_version': '0.0.0.1',
        'tags': ['wechat', 'wx', 'Sleepy'],
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

wechatRobot: Bot = None
subServiceContext: SubServiceContext = None


# ----------------------------------------------------------------------------------------------------------------------

def user_message_handler(msg):
    print(msg)


def group_message_handler(msg):
    print(msg)


# ----------------------------------------------------------------------------------------------------------------------

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
    global wechatRobot
    wechatRobot = Bot()

    @wechatRobot.register(User, TEXT)
    def user_message(msg):
        user_message_handler(msg)

    @wechatRobot.register(Group, TEXT)
    def group_message(msg):
        group_message_handler(msg)

    return True


def thread(context: dict):
    wechatRobot.join()


def polling(interval_ns: int):
    print('Period...' + str(interval_ns))
    pass


def event_handler(event: Event, **kwargs):
    print('Event')
    pass

