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


class SourceCollector:
    def __init__(self, collector_plugin: PluginManager):
        self.__plugin_manager = collector_plugin

    def query(self, uri: str, identity: str or [str] = None,
              time_serial: tuple = None, **extra) -> pd.DataFrame or None:
        argv = self.pack_query_params(uri, identity, time_serial, **extra)
        plugins = self.get_plugin_manager().find_module_has_capacity(uri)
        for plugin in plugins:
            result = self.get_plugin_manager().execute_module_function(plugin, 'query', argv)
            df = result[0] if len(result) > 0 else None
            if df is not None and isinstance(df, pd.DataFrame) and len(df) > 0:
                return df
        return None

    # ---------------------------------------------------------------------------------------------------

    def get_plugin_manager(self) -> PluginManager:
        return self.__plugin_manager

    def pack_query_params(self, uri: str, identity: str or [str], time_serial: tuple, **extra) -> dict:
        table, _ = self.get_data_table(uri)

        if table is not None:
            identity_field = table.identity_field()
            datetime_field = table.datetime_field()
        else:
            identity_field = None
            datetime_field = None

        if not NoSqlRw.str_available(identity_field):
            identity_field = 'identity'
        if not NoSqlRw.str_available(datetime_field):
            datetime_field = 'datetime'

        pack = {'uri': uri}
        if extra is not None:
            pack.update(extra)
        if str_available(identity) and str_available(identity_field):
            pack[identity_field] = identity
        if time_serial is not None and str_available(datetime_field):
            pack[datetime_field] = time_serial
        return pack




















