import openpyxl
import datetime
import pandas as pd
from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    import config
    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
except Exception as e:
    sys.path.append(root_path)

    import config
    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
finally:
    pass


def dispatch_calculation_pattern(factor: str, identity: str or [str], time_serial: tuple, mapping: dict,
                                 data_hub: DataHubEntry, database: DatabaseEntry, extra: dict,
                                 FACTOR_TABLE) -> pd.DataFrame or None:
    for uuid, prob in FACTOR_TABLE.items():
        if prob is None or len(prob) != 7:
            continue
        provides, depends, comments, entry, _, _, _ = prob
        if factor in provides:
            return entry(identity, time_serial, mapping, data_hub, database, extra)
    return None


def query_finance_pattern(data_hub: DataHubEntry, identity: str,
                          time_serial: tuple, fields: list, mapping: dict) -> pd.DataFrame:
    query_fields = [mapping.get(f, f) for f in fields]
    query_fields = list(set(query_fields))

    if 'period' in query_fields:
        query_fields.remove('period')
    if 'stock_identity' in query_fields:
        query_fields.remove('stock_identity')

    data_utility = data_hub.get_data_utility()
    df = data_utility.auto_query(identity, time_serial, query_fields, join_on=['stock_identity', 'period'])

    df.fillna(0.0, inplace=True)
    df = df.sort_values('period', ascending=False)

    return df











