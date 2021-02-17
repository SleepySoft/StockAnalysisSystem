import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.event_queue import Event
from StockAnalysisSystem.core.SubServiceManager import SubServiceContext

# 事件入口
#    定时事件
#    调用事件
#    订阅事件

# 线程入口
# Polling入口

# 注册系统调用


SERVICE_ID = '7129e9d2-4f53-4826-9161-c568ced52d02'

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': SERVICE_ID,
        'plugin_name': 'Dummy',
        'plugin_version': '0.0.0.1',
        'tags': ['Dummy', 'Test', 'Example', 'Sleepy'],
    }


def plugin_adapt(service: str) -> bool:
    return service == SERVICE_ID


def plugin_capacities() -> list:
    return []
    # return [
    #     'api',            # Provides functions like sys call
    #     'thread',         # SubService manager will create a thread for this service
    #     'polling',        # polling() function will be invoked while event processing thread is free
    #     'event_handler'   # SubService can handle events that dispatch to it
    # ]


# ----------------------------------------------------------------------------------------------------------------------

subServiceContext: SubServiceContext = None


def init(sub_service_context: SubServiceContext) -> bool:
    """
    System will invoke this function before startup() once. The initialization order of service is uncertain.
    :param sub_service_context: The instance of SubServiceContext
    :return: True if successful else False
    """
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
    """
    System will invoke this function after all service being initialized and service before activated.
    You and put the cross-service invoking here.
    """
    return True


def thread(context: dict):
    """
    If you specify 'thread' in plugin_capacities(). This function will be invoked in a thread.
    If this function returns or has uncaught exception, the thread will be terminated and will not restart again.
    :param context: The context from StockAnalysisSystem, includes:
                    'quit_flag': bool - Process should be terminated and quit this function if it's True.
                    '?????????': any  - TBD
    :return: None
    """
    print('Thread...')
    pass


def polling(interval_ns: int):
    """
    If you specify 'polling' in plugin_capacities(). This function will be invoked when event queue is free.
    Note that if this extension spends too much time on this function. The interface will be blocked.
    And this extension will be removed from running list.
    :param interval_ns: The interval between previous invoking and now.
    :return: None
    """
    print('Period...' + str(interval_ns))
    pass


def event_handler(event: Event, **kwargs):
    """
    Use this function to handle event. Includes timer and subscribed event.
    :param event: The event data
    :return:
    """
    print('Event')
    pass




