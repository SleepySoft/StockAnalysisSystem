import pandas as pd
from datetime import datetime


def plugin_prob() -> dict:
    return {
        'plugin_name': 'dummy_plugin_for_test',
        'plugin_version': '0.0.0.1',
        'tags': ['example', 'collector']
    }


def plugin_adapt(uri: str) -> bool:
    return uri == 'Example.Collector'


def plugin_capacities() -> list:
    return [
        'Example.Collector',
    ]


def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri == 'Example.Collector':
        return pd.DataFrame({
            'id': ['StockA', 'StockA', 'StockB', 'StockB', 'StockC', 'StockC'],
            'time': [datetime(1995, 1, 1), datetime(1996, 1, 1),    # StockA
                     datetime(2002, 2, 1), datetime(2005, 5, 1),    # StockB
                     datetime(2020, 3, 1), datetime(2021, 1, 1)],   # StockC
            'field1': [10., 20., 30., 40., 50., 60.],
            'field2': ['A', 'B', 'C', 'D', 'E', 'F'],
        })
    else:
        return None


def nop(*args):
    pass


def validate(**kwargs) -> bool:
    nop(kwargs)
    return True


def fields() -> dict:
    return {}



















































