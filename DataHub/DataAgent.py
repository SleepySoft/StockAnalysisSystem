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


class DataAgent:
    DEFAULT_SINCE_DATE = default_since()

    DATA_DURATION_AUTO = 0          # Not specify
    DATA_DURATION_NONE = 10         # Data without timestamp
    DATA_DURATION_FLOW = 50         # Data with uncertain timestamp
    DATA_DURATION_DAILY = 100       # Daily data
    DATA_DURATION_QUARTER = 500     # Quarter data
    DATA_DURATION_ANNUAL = 1000     # Annual Data

    # ------------------------------- DataAgent -------------------------------

    def __init__(self,
                 uri: str, database_entry: DatabaseEntry,
                 depot_name: str, table_prefix: str = '',
                 identity_field: str or None = 'Identity',
                 datetime_field: str or None = 'DateTime'):
        """
        If you specify both identity_field and datetime_field, the combination will be the primary key. Which means
            an id can have multiple different time serial record. e.g. stock daily price table.
        If you only specify the identity_field, the identity_field will be the only primary key. Which means
            its a time independent serial record with id. e.g. stock information table
        If you only specify the datetime_field, the datetime_field will be the only primary key. Which means
            it's a time serial record without id. e.g. log table
        If you do not specify neither identity_field and datetime_field, the table has not primary key. Which means
            the table cannot not updated by id or time. Record is increase only except update by manual.
        :param uri: The URI of the resource.
        :param database_entry: The instance of DatabaseEntry.
        :param depot_name: The name of database.
        :param table_prefix: The prefix of table, default empty.
        :param identity_field: The identity filed name.
        :param datetime_field: The datetime filed name.
        """
        self.__uri = uri
        self.__database_entry = database_entry
        self.__depot_name = depot_name
        self.__table_prefix = table_prefix
        self.__identity_field = identity_field
        self.__datetime_field = datetime_field

        # -------------------------------------------------------------------

    def base_uri(self) -> str:
        return self.__uri

    def database_entry(self) -> DatabaseEntry:
        return self.__database_entry

    def depot_name(self) -> str:
        return self.__depot_name

    def table_prefix(self) -> str:
        return self.__table_prefix

    def identity_field(self) -> str or None:
        return self.__identity_field

    def datetime_field(self) -> str or None:
        return self.__datetime_field

    def data_duration(self) -> int:
        nop(self)
        return DataAgent.DATA_DURATION_AUTO

    # -------------------------------------------------------------------

    def merge_on_column(self) -> list:
        on_column = []
        if str_available(self.__identity_field):
            on_column.append(self.__identity_field)
        if str_available(self.__datetime_field):
            on_column.append(self.__datetime_field)
        return on_column

    def ref_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        nop(self, uri, identity)
        return None, None

    def table_name(self, uri: str, identity: str or [str], time_serial: tuple, extra: dict, fields: list) -> str:
        nop(self, identity, time_serial, extra, fields)
        return self.table_prefix() + uri.replace('.', '_')

    # -------------------------------------------------------------------

    def adapt(self, uri: str) -> bool:
        return self.__uri.lower() == uri.lower()

    def query(self, uri: str, identity: str or [str], time_serial: tuple,
              extra: dict, fields: list) -> pd.DataFrame or None:
        table = self.data_table(uri, identity, time_serial, extra, fields)
        since, until = normalize_time_serial(time_serial)
        result = table.query(identity, since, until, extra, fields)
        df = pd.DataFrame(result)
        return df

    def merge(self, uri: str, identity: str, df: pd.DataFrame):
        table = self.data_table(uri, identity, (None, None), {}, [])
        identity_field, datetime_field = table.identity_field(), table.datetime_field()

        table.set_connection_threshold(1)
        for index, row in df.iterrows():
            identity_value = None
            if NoSqlRw.str_available(identity_field):
                if identity_field in list(row.index):
                    identity_value = row[identity_field]
            if NoSqlRw.str_available(identity_field) and identity_value is None:
                print('Warning: identity field "' + identity_field + '" of <' + uri + '> missing.')
                continue

            datetime_value = None
            if NoSqlRw.str_available(datetime_field):
                if datetime_field in list(row.index):
                    datetime_value = row[datetime_field]
                    if isinstance(datetime_value, str):
                        datetime_value = text_auto_time(datetime_value)
            if NoSqlRw.str_available(datetime_field) and datetime_value is None:
                print('Warning: datetime field "' + datetime_field + '" of <' + uri + '> missing.')
                continue
            table.bulk_upsert(identity_value, datetime_value, row.dropna().to_dict())
        table.bulk_flush()

    def range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        table = self.data_table(uri, identity, (None, None), {}, [])
        return (table.min_of(self.datetime_field(), identity), table.max_of(self.datetime_field(), identity)) \
            if str_available(self.datetime_field()) else (None, None)

    def update_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        local_since, local_until = self.range(uri, identity)
        ref_since, ref_until = self.ref_range(uri, identity)
        return local_until, ref_until

    def data_table(self, uri: str, identity: str or [str],
                   time_serial: tuple, extra: dict, fields: list) -> NoSqlRw.ItkvTable:
        table_name = self.table_name(uri, identity, time_serial, extra, fields)
        return self.__database_entry.query_nosql_table(self.__depot_name, table_name,
                                                       self.__identity_field, self.__datetime_field)


# ----------------------------------------------------------------------------------------------------------------------

class DataAgentSecurityDaily(DataAgent):
    def __init__(self,
                 uri: str, database_entry: DatabaseEntry,
                 depot_name: str, table_prefix: str = '',
                 identity_field: str or None = 'Identity',
                 datetime_field: str or None = 'DateTime'):
        super(DataAgentSecurityDaily, self).__init__(
            uri, database_entry, depot_name, table_prefix, identity_field, datetime_field)

    def data_duration(self) -> int:
        nop(self)
        return DataAgent.DATA_DURATION_DAILY

    def table_name(self, uri: str, identity: str, time_serial: tuple, extra: dict, fields: list) -> str:
        name = (uri + '_' + identity) if str_available(identity) else uri
        return name.replace('.', '_')

    def query(self, uri: str, identity: str or [str], time_serial: tuple,
              extra: dict, fields: list) -> pd.DataFrame or None:
        result = None
        for _id in identity:
            df = super(DataAgentSecurityDaily, self).query(uri, _id, time_serial, extra, fields)
            if df is None or len(df) == 0:
                continue
            result = df if result is None else pd.merge(result, df, on=self.merge_on_column())
        return result


class DataAgentFactorQuarter(DataAgent):
    def __init__(self,
                 uri: str, database_entry: DatabaseEntry,
                 depot_name: str, table_prefix: str = '',
                 identity_field: str or None = 'Identity',
                 datetime_field: str or None = 'DateTime'):
        super(DataAgentFactorQuarter, self).__init__(
            uri, database_entry, depot_name, table_prefix, identity_field, datetime_field)

    def data_duration(self) -> int:
        nop(self)
        return DataAgent.DATA_DURATION_QUARTER

    def adapt(self, uri: str) -> bool:
        return 'factor' in uri.lower() and 'daily' not in uri.lower()


class DataAgentFactorDaily(DataAgentSecurityDaily):
    def __init__(self,
                 uri: str, database_entry: DatabaseEntry,
                 depot_name: str, table_prefix: str = '',
                 identity_field: str or None = 'Identity',
                 datetime_field: str or None = 'DateTime'):
        super(DataAgentFactorDaily, self).__init__(
            uri, database_entry, depot_name, table_prefix, identity_field, datetime_field)

    def data_duration(self) -> int:
        nop(self)
        return DataAgent.DATA_DURATION_QUARTER

    def adapt(self, uri: str) -> bool:
        return 'factor' in uri.lower() and 'daily' not in uri.lower()


# ----------------------------------------------------------------------------------------------------------------------

class DataAgentFactory:
    def __init__(self):
        pass

    @staticmethod
    def create_data_agent(self, uri: str, *args, **kwargs) -> DataAgent:
        uri = uri.lower()
        if uri.lower().startswith('factor'):
            if uri.endswith('daily'):
                return DataAgentFactorDaily(uri, *args, **kwargs)
            else:
                return DataAgentFactorQuarter(uri, *args, **kwargs)
        else:
            if uri.endswith('daily'):
                return DataAgentSecurityDaily(uri, *args, **kwargs)
        return DataAgent(uri, *args, **kwargs)










