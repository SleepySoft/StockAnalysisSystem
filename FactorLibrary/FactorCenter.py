import sys
import datetime
import traceback
import pandas as pd

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Database import NoSqlRw
    from Database import UpdateTableEx
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
except Exception as e:
    sys.path.append(root_path)

    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Database import NoSqlRw
    from Database import UpdateTableEx
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
finally:
    logger = logging.getLogger('')


class FactorCenter:
    def __init__(self, factor_plugin: PluginManager):
        self.__factor_plugin = factor_plugin

    def query(self, factor_name: [str], time_serial: tuple, extra: dict) -> pd.DataFrame or None:
        pass

    def has_factor(self, factor_name: str) -> bool:
        pass

    def all_factors(self) -> [str]:
        pass

    def factor_identity(self, factor_name: str) -> str:
        pass

    def reload_plugin(self):
        pass

    def calculate_factor(self, factor_name: [str]):
        pass

    def factor_from_cache(self):
        pass

























