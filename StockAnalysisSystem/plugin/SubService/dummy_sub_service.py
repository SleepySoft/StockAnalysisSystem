import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.sub_service_util import ServiceEvent

# 事件入口
#    定时事件
#    调用事件
#    订阅事件

# 线程入口
# Polling入口

# 注册系统调用

# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': '47127b1b-88d1-43a9-b4aa-94819c1a73f7',
        'plugin_name': 'Dummy',
        'plugin_version': '0.0.0.1',
        'tags': ['Dummy', 'Test', 'Example', 'Sleepy'],
    }


def plugin_adapt(service: str) -> bool:
    return service in ['47127b1b-88d1-43a9-b4aa-94819c1a73f7']


def plugin_capacities() -> list:
    return []
    # return [
    #     'period',
    #     'thread',
    #     'on_event'
    # ]


# ----------------------------------------------------------------------------------------------------------------------

sasApiEntry: sasApi = None


def init(sas_api: sasApi) -> bool:
    """
    System will invoke this function at startup once.
    :param sas_api: The sasApi entry
    :return: True if successful else False
    """
    try:
        global sasApiEntry
        sasApiEntry = sas_api
    except Exception as e:
        pass
    finally:
        pass
    return True


def period(interval_ns: int):
    """
    If you specify 'period' in plugin_capacities(). This function will be invoked periodically by MAIN thread,
        the invoke interval should be more or less than 100ms.
    Note that if this extension spends too much time on this function. The interface will be blocked.
    And this extension will be removed from running list.
    :param interval_ns: The interval between previous invoking and now.
    :return: None
    """
    print('Period...' + str(interval_ns))
    pass


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


def on_event(event: ServiceEvent):
    """
    Use this function to handle event. Includes timer and subscribed event.
    :param event: The event data
    :return:
    """
    print('Event')
    pass




