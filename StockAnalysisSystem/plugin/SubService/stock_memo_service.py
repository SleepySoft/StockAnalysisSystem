import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.event_queue import ServiceEvent


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': 'bd9a7d9f-dbcc-4dc8-8992-16dac9191ff9',
        'plugin_name': 'Stock Memo',
        'plugin_version': '0.0.0.1',
        'tags': ['stock_memo', 'Sleepy'],
    }


def plugin_adapt(method: str) -> bool:
    return method in ['bd9a7d9f-dbcc-4dc8-8992-16dac9191ff9']


def plugin_capacities() -> list:
    return [
        'period',
        'thread',
        'on_event'
    ]


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











