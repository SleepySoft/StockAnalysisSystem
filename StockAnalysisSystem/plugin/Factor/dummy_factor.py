import pandas as pd

from StockAnalysisSystem.core.Utiltity.FactorUtility import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.Database.DatabaseEntry import DatabaseEntry


FACTOR_LIST = {
    # uuid: (provides, depends, comments, entry, reserve1, reserve2, reserve3)
}


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': 'cc43c66a-dabd-45a8-9698-b32e1817536d',
        'plugin_name': 'DummyFactor',
        'plugin_version': '0.0.0.1',
        'tags': ['Dummy', 'Factor', 'Sleepy'],
        'factor': FACTOR_LIST,
    }


def plugin_capacities() -> list:
    return []


# ----------------------------------------------------------------------------------------------------------------------

def calculate(factor: [str], identity: str or [str], time_serial: tuple, mapping: dict,
              data_hub: DataHubEntry, database: DatabaseEntry, extra: dict) -> pd.DataFrame:
    return None













