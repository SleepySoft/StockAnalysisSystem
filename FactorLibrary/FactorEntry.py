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
    from FactorLibrary.FactorCenter import FactorCenter
except Exception as e:
    sys.path.append(root_path)

    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Database import NoSqlRw
    from Database import UpdateTableEx
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
    from FactorLibrary.FactorCenter import FactorCenter
finally:
    logger = logging.getLogger('')


class FactorEntry:
    def __init__(self, factor_plugin: PluginManager):
        self.__factor_plugin = factor_plugin
        self.__factor_center = FactorCenter(factor_plugin)

    def get_factor_center(self) -> FactorCenter:
        return self.__factor_center





















