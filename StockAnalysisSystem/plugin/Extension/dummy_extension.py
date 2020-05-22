from PyQt5.QtWidgets import QWidget

from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': 'e4b259f1-9d6a-498a-b0de-ce7c83d9938d',
        'plugin_name': 'Dummy',
        'plugin_version': '0.0.0.1',
        'tags': ['Dummy', 'Test', 'Example', 'Sleepy'],
    }


def plugin_adapt(method: str) -> bool:
    return method in ['widget']


def plugin_capacities() -> list:
    return []
    # return [
    #     'period',
    #     'thread',
    #     'widget',
    # ]


# ----------------------------------------------------------------------------------------------------------------------

sasEntry = None


def init(sas: StockAnalysisSystem) -> bool:
    """
    System will invoke this function at startup once.
    :param sas: The instance of StockAnalysisSystem
    :return: True if successful else False
    """
    try:
        global sasEntry
        sasEntry = sas
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


def widget(parent: QWidget) -> (QWidget, dict):
    """
    If you sepcify 'widget' in plugin_capacities(). This function will be invoked once at startup.
    You should create and return a widget and it's config as a dict.
    :param parent: The parent widget to create your widget.
    :return: A tuple includes a QWidget and a dict.
                QWidget: The widget you want to embed in the main widget.
                dict   : The widget config in a dict.
                    'name': str  - The name of this widget. Will be used as the title of its entry.
                    'show': bool - Show at startup if True, else False
    """
    print('Widget...')
    return None


















