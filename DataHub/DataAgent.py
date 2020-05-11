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


# --------------------------------------------- Data Declaration Functions ---------------------------------------------

# --------------------- Update List ---------------------

def a_stock_list() -> [str]:
    pass


def hk_stock_list() -> [str]:
    return []


def support_stock_list() -> [str]:
    return a_stock_list() + hk_stock_list()


def support_index_list() -> [str]:
    pass


def support_exchange_list() -> [str]:
    pass


# ------------------------ Splitter ------------------------

def split_none(uri: str, identity: str or [str], time_serial: tuple, extra: dict, fields: list) -> \
        [(str, str or [str], tuple, dict, list)]:
    return uri, identity, time_serial, extra, fields


def split_by_identity(uri: str, identity: str or [str], time_serial: tuple, extra: dict, fields: list) -> \
        [(str, str or [str], tuple, dict, list)]:
    if not isinstance(identity, (list, tuple)):
        identity = [identity]
    return [(uri, _id, time_serial, extra, fields) for _id in identity]


# ------------------------ Time Node ------------------------

def stock_listing(securities: str) -> datetime.datetime:
    pass


def a_share_market_start(securities: str) -> datetime.datetime:
    return text_auto_time('1990-12-19')


def latest_day(securities: str) -> datetime.datetime:
    pass


def latest_quarter(securities: str) -> datetime.datetime:
    pass


def latest_trade_day(securities: str) -> datetime.datetime:
    pass


# ---------------------------------------------- Data Declaration Element ----------------------------------------------

UPDATE_LIST_STOCK = support_stock_list
UPDATE_LIST_INDEX = support_index_list
UPDATE_LIST_EXCHANGE = support_exchange_list

KEY_TYPE_UNIQUE = 1
KEY_TYPE_GROUP = 2

SPLIT_NONE = split_none
SPLIT_BY_IDENTITY = split_by_identity

TIME_STOCK_LISTING = stock_listing
TIME_A_SHARE_MARKET_START = a_share_market_start

TIME_TODAY = latest_day
TIME_LATEST_QUARTER = latest_quarter
TIME_LATEST_TRADE_DAY = latest_trade_day

DATA_DURATION_AUTO = 0  # Not specify
DATA_DURATION_NONE = 10  # Data without timestamp
DATA_DURATION_FLOW = 50  # Data with uncertain timestamp
DATA_DURATION_DAILY = 100  # Daily data
DATA_DURATION_QUARTER = 500  # Quarter data
DATA_DURATION_ANNUAL = 1000  # Annual Data

# ----------------------------------------------------------------------------------------------------------------------


class DataAgent:
    DEFAULT_SINCE_DATE = default_since()

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

        self.identity_update_list = None
        self.data_since = None
        self.data_until = None
        self.data_duration = None
        self.query_split = None
        self.merge_split = None
        self.checker = None

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


class ParameterChecker:

    """
    Key: str - The key you need to check in the dict param
    Val: tuple - The first item: The list of expect types for this key, you can specify a None if None is allowed
                 The second item: The list of expect values for this key, an empty list means it can be any value
                 The third item: True if it's necessary, False if it's optional.
    DICT_PARAM_INFO_EXAMPLE = {
        'identity':     ([str], ['id1', 'id2'], True),
        'datetime':     ([datetime.datetime, None], [], False)
    }

    The param info for checking a dataframe.
    It's almost likely to the dict param info except the type should be str instead of real python type
    DATAFRAME_PARAM_INFO_EXAMPLE = {
        'identity':         (['str'], [], False),
        'period':           (['datetime'], [], True)
    }
    """

    PYTHON_DATAFRAME_TYPE_MAPPING = {
        'str': 'object',
        'list': 'object',
        'dict': 'object',
        'int': 'int64',
        'float': 'float64',
        'datetime': 'datetime64[ns]',
    }

    def __init__(self, df_param_info: dict = None, dict_param_info: dict = None):
        self.__df_param_info = df_param_info
        self.__dict_param_info = dict_param_info

    def check_dict(self, argv: dict) -> bool:
        if self.__dict_param_info is None or len(self.__dict_param_info) == 0:
            return True
        return ParameterChecker.check_dict_param(argv, self.__dict_param_info)

    def check_dataframe(self, df: dict) -> bool:
        if self.__df_param_info is None or len(self.__df_param_info) == 0:
            return True
        return ParameterChecker.check_dataframe_field(df, self.__df_param_info)

    @staticmethod
    def check_dict_param(argv: dict, param_info: dict) -> bool:
        if argv is None or len(argv) == 0:
            return False
        keys = list(argv.keys())

        for param in param_info.keys():
            types, values, must, _ = param_info[param]

            if param not in keys:
                if must:
                    logger.info('Param key check error: Param is missing - ' + param)
                    return False
                else:
                    continue

            value = argv[param]
            if value is None and None in types:
                continue
            if not isinstance(value, tuple([t for t in types if t is not None])):
                logger.info('Param key check error: Param type mismatch - ' +
                            str(type(value)) + ' is not in ' + str(types))
                return False

            if len(values) > 0:
                if value not in values:
                    logger.info('Param key check error: Param value out of range - ' +
                                str(value) + ' is not in ' + str(values))
                    return False
        return True

    @staticmethod
    def check_dataframe_field(df: pd.DataFrame, field_info: dict) -> bool:
        """
        Check whether DataFrame filed fits the field info.
        :param df: The DataFrame you want to check
        :param field_info: The definition of fields info
        :return: True if all fields are satisfied. False if not.
        """
        if df is None or len(df) == 0:
            return False
        columns = list(df.columns)

        for field in field_info.keys():
            types, values, must, _ = field_info[field]

            if field not in columns:
                if must:
                    logger.info('DataFrame field check error: Field is missing - ' + field)
                    return False
                else:
                    continue

            type_ok = False
            type_df = df[field].dtype
            for py_type in types:
                df_type = ParameterChecker.PYTHON_DATAFRAME_TYPE_MAPPING.get(py_type)
                if df_type is not None and df_type == type_df:
                    type_ok = True
                    break
            if not type_ok:
                logger.info('DataFrame field check error: Field type mismatch - ' +
                            field + ': ' + str(df_type) + ' not match ' + str(type_df))
                return False

            if len(values) > 0:
                out_of_range_values = df[~df[field].isin(values)]
                if len(out_of_range_values) > 0:
                    logger.info('DataFrame field check error: Field value out of range - ' +
                                str(out_of_range_values) + ' is not in ' + str(values))
                    return False
        return True


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
    NO_SQL_ENTRY = None

    def __init__(self):
        pass

    @staticmethod
    def create_data_agent(uri: str, database: str, table_prefix: str, 
                          identity_field: str or None, datetime_field: str or None, **argv) -> DataAgent:
        """

        :param uri:
        :param database:
        :param table_prefix:
        :param identity_field:
        :param identity_update_list:
        :param datetime_field:
        :param data_since:
        :param data_until:
        :param data_duration:
        :param extra_key:
        :param key_type:
        :param table_name:
        :param query_split:
        :param merge_split:
        :param query_declare:
        :param result_declare:
        :param argv:
        :return:
        """

        data_agent = DataAgent(uri, DataAgentFactory.NO_SQL_ENTRY,
                               database, table_prefix, identity_field, datetime_field)

        data_agent.identity_update_list = argv.get('identity_update_list', None)

        data_agent.data_since = argv.get('data_since', None)
        data_agent.data_until = argv.get('data_until', None)
        data_agent.data_duration = argv.get('data_duration', None)

        data_agent.extra_key = argv.get('extra_key', None)
        data_agent.key_type = argv.get('key_type', None)
        data_agent.table_name = argv.get('table_name', None)

        data_agent.query_split = argv.get('query_split', None)
        data_agent.merge_split = argv.get('merge_split', None)

        data_agent.checker = ParameterChecker(argv.get('query_declare', None), argv.get('result_declare', None))


DECLARE_DATA_AGENT = DataAgentFactory.create_data_agent








