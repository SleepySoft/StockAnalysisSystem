



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


def collect_factor_depends_fields(factor_identities:[str]):
    pass


def standard_apply_factor(df: pd.DataFrame, factor_identities:[str],
                          factor_table: dict, **extra) -> pd.DataFrame or None:
    # 1.Check the fields full filled
    # 2.Find factor calculator and transfer parameter to it
    # 1.
    pass












