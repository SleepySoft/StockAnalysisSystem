import pandas as pd
from datetime import date

from os import sys, path

from PyQt5.QtWidgets import QWidget

root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
    from stock_analysis_system import StockAnalysisSystem
except Exception as e:
    sys.path.append(root_path)

    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
    from stock_analysis_system import StockAnalysisSystem
finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': 'b3767a36-123f-45ab-bfad-f352c2b48354',
        'plugin_name': 'History',
        'plugin_version': '0.0.0.1',
        'tags': ['History', 'Sleepy'],
    }


def plugin_adapt(method: str) -> bool:
    return method in ['widget']


def plugin_capacities() -> list:
    return [
        'widget',
    ]


# ----------------------------------------------------------------------------------------------------------------------

def init(sas: StockAnalysisSystem):
    try:
        from Extension.History.main import HistoryUi
        main_wnd = HistoryUi()
    except Exception as e:
        main_wnd = None
    finally:
        pass
    return main_wnd


def period():
    pass


def thread():
    pass


def widget() -> QWidget:
    pass


















