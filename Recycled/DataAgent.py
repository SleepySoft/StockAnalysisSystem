import datetime
import pandas as pd

from ..Utiltity.common import *
from ..UniversalDataDepot import *
from ..Utiltity.df_utility import *
from ..Utiltity.time_utility import *
from ..Database.NoSqlRw import ItkvTable
from ..Database.DatabaseEntry import DatabaseEntry
from ..StockAnalysisSystem import StockAnalysisSystem
from .ParameterChecker import ParameterChecker

logger = logging.getLogger('')


# --------------------------------------------- Data Declaration Functions ---------------------------------------------

class DataAgentUtility:
    @staticmethod
    def data_utility():
        sas = StockAnalysisSystem()
        return sas.get_data_hub_entry().get_data_utility() if sas.is_initialized() else None

    # ------------------------ Update List ------------------------

    @staticmethod
    def a_stock_list() -> [str]:
        data_utility = DataAgentUtility.data_utility()
        return data_utility.get_stock_identities()

    @staticmethod
    def hk_stock_list() -> [str]:
        return []

    @staticmethod
    def support_stock_list() -> [str]:
        return DataAgentUtility.a_stock_list() + DataAgentUtility.hk_stock_list()

    @staticmethod
    def support_index_list() -> [str]:
        data_utility = DataAgentUtility.data_utility()
        return list(data_utility.get_support_index().keys())

    @staticmethod
    def support_exchange_list() -> [str]:
        data_utility = DataAgentUtility.data_utility()
        return list(data_utility.get_support_exchange().keys())

    # ------------------------ Time Node ------------------------

    @staticmethod
    def stock_listing(securities: str) -> datetime.datetime:
        data_utility = DataAgentUtility.data_utility()
        return data_utility.get_stock_listing_date(securities, DataAgentUtility.a_share_market_start())

    @staticmethod
    def a_share_market_start() -> datetime.datetime:
        return text_auto_time('1990-12-19')

    @staticmethod
    def latest_day() -> datetime.datetime:
        return today()

    @staticmethod
    def latest_quarter() -> datetime.datetime:
        return previous_quarter(today())

    @staticmethod
    def latest_trade_day() -> datetime.datetime:
        return today()


# ----------------------------------------------------------------------------------------------------------------------

DATA_DURATION_AUTO = 0  # Not specify
DATA_DURATION_NONE = 10  # Data without timestamp
DATA_DURATION_FLOW = 50  # Data with uncertain timestamp
DATA_DURATION_DAILY = 100  # Daily data
DATA_DURATION_QUARTER = 500  # Quarter data
DATA_DURATION_ANNUAL = 1000  # Annual Data


# ----------------------------------------------------------------------------------------------------------------------

# In order to describe accurately, we'll use Chinese for following comments.
#
# 使用或扩展DataAgent需要考虑以下问题：
# 构造参数：
#   0.常规操作：uri，database_entry，table_prefix，不用多解释
#   1.使用哪个数据库？(depot_name)
#   2.此数据是否需要identity作为存储的索引？如果是，使用什么字段（identity_field）
#   3.此数据是否使用datetime作为存储的索引？如果是，使用什么字段（datetime_field）
#   4.此数据是否还使用其它字段作为存储的索引？如果是，还有哪些字段（extra_key） - 待实现
#   5.数据的周期（相同周期的数据可以简单合并在一起）（duration）；高级需求可以重写data_duration()
# 函数重载：
#   6.URI使用简单匹配（转小写比较）是否满足需要？如果否，重写adapt()
#   7.你希望为数据指定确切的范围吗（便于增量更新判断）？如果是，重写ref_range()
#   8.默认的merge_on（identity_field + datetime_field + extra_key）满足需要吗？如果否，重写mergeable_n_on()
#   9.默认的table_name满足需要吗（简单将uri中的点替换成下划线作为数据库表名）？如果否，重写tame()
#   10.是否希望提供详细的更新列表，以便更新数据时使用？如果是，重写update_list()
#   11.默认的查询（单表查询）是否满足需要？如果否，重写query()
#   12.默认的合并数据（合并到单表）是否满足需要？如果否，重写merge()
#

class DataAgent:
    def __init__(self,
                 uri: str, database_entry: DatabaseEntry,
                 depot_name: str, table_prefix: str = '',
                 identity_field: str or None = 'Identity',
                 datetime_field: str or None = 'DateTime',
                 candidate_fields: tuple or None = None,
                 **kwargs):
        """
        If you specify both identity_field and datetime_field, the combination will be the primary key. Which means
            an id can have multiple different time serial record. e.g. stock daily price table.
        If you only specify the identity_field, the identity_field will be the only primary key. Which means
            its a time independent serial record with id. e.g. stock information table
        If you only specify the datetime_field, the datetime_field will be the only primary key. Which means
            it's a time serial record without id. e.g. log table
        If you do not specify neither identity_field and datetime_field, the table has not primary key. Which means
            the table cannot not updated by id or time. Record is increase only except update by manual.
        """
        self.__uri = uri
        self.__database_entry = database_entry
        self.__depot_name = depot_name
        self.__table_prefix = table_prefix
        self.__identity_field = identity_field
        self.__datetime_field = datetime_field
        self.__candidate_fields = candidate_fields
        self.__checker = None
        self.__extra = kwargs

        self.config_field_checker(kwargs.get('query_declare', None), kwargs.get('result_declare', None))

    # ---------------------------------- Constant ----------------------------------

    def base_uri(self) -> str:
        return self.__uri

    def depot_name(self) -> str:
        return self.__depot_name

    def table_prefix(self) -> str:
        return self.__table_prefix

    def identity_field(self) -> str or None:
        return self.__identity_field

    def datetime_field(self) -> str or None:
        return self.__datetime_field

    def extra_param(self, key: str, default: any = None) -> any:
        return self.__extra.get(key, default)

    def database_entry(self) -> DatabaseEntry:
        return self.__database_entry

    def data_table(self, uri: str, identity: str or [str],
                   time_serial: tuple, extra: dict, fields: list) -> ItkvTable:
        table_name = self.table_name(uri, identity, time_serial, extra, fields)
        return self.__database_entry.query_nosql_table(self.__depot_name, table_name,
                                                       self.__identity_field, self.__datetime_field)
        
    def get_field_checker(self) -> ParameterChecker:
        return self.__checker

    def config_field_checker(self, query_declare: dict, result_declare: dict):
        if query_declare is not None or result_declare is not None:
            self.__checker = ParameterChecker(result_declare, query_declare)

    # ------------------------------- Overrideable -------------------------------

    def adapt(self, uri: str) -> bool:
        return self.__uri.lower() == uri.lower()

    def data_duration(self) -> int:
        nop(self)
        return self.extra_param('duration', DATA_DURATION_AUTO)

    def ref_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        nop(self, uri, identity)
        return None, None

    def data_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        table = self.data_table(uri, identity, (None, None), {}, [])
        return (table.min_of(self.datetime_field(), identity), table.max_of(self.datetime_field(), identity)) \
            if str_available(self.datetime_field()) else (None, None)

    def update_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        local_since, local_until = self.data_range(uri, identity)
        ref_since, ref_until = self.ref_range(uri, identity)
        return local_until, ref_until

    def merge_on(self) -> list:
        on_column = []
        if str_available(self.__identity_field):
            on_column.append(self.__identity_field)
        if str_available(self.__datetime_field):
            on_column.append(self.__datetime_field)
        on_column += self.extra_param('extra_key', [])
        return on_column

    def table_name(self, uri: str, identity: str or [str], time_serial: tuple, extra: dict, fields: list) -> str:
        nop(self, identity, time_serial, extra, fields)
        return self.table_prefix() + uri.replace('.', '_')

    def update_list(self) -> [str]:
        nop(self)
        return []

    # ------------------------------ Overrideable but -------------------------------------

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

        identity_field_available = str_available(identity_field)
        datetime_field_available = str_available(datetime_field)

        table.set_connection_threshold(1)

        # for index, row in df.iterrows():
        # for row in df.to_dict(orient='records'):
        # https://stackoverflow.com/a/46098323/12929244
        # rows = [{k: v for k, v in m.items() if pd.notnull(v)} for m in df.to_dict(orient='rows')]
        rows = [{k: v for k, v in m.items() if v == v and v is not None} for m in df.to_dict(orient='r')]
        for row in rows:
            identity_value = row.get(identity_field, None) if identity_field_available else None
            if identity_field_available and identity_value is None:
                print('Warning: identity field "' + identity_field + '" of <' + uri + '> missing.')
                continue

            datetime_value = row.get(datetime_field, None) if datetime_field_available else None
            if isinstance(datetime_value, str):
                datetime_value = text_auto_time(datetime_value)
            if datetime_field_available and datetime_value is None:
                print('Warning: datetime field "' + datetime_field + '" of <' + uri + '> missing.')
                continue
            table.bulk_upsert(identity_value, datetime_value, row)          # row.dropna().to_dict())
        table.bulk_flush()

    def merge2(self, uri: str, identity: str, _data: pd.DataFrame or dict or [dict]):
        if isinstance(_data, pd.DataFrame):
            clock = Clock()
            data_dict = _data.T.apply(lambda x: x.dropna().to_dict()).tolist()
            # data_dict = _data.T.to_dict().values()
            print('Convert DataFrame size(%d) time spending: %s' % (len(_data), clock.elapsed_s()))
        elif isinstance(_data, dict):
            data_dict = [_data]
        elif isinstance(_data, (list, tuple)):
            data_dict = _data
        else:
            return
        
        table = self.data_table(uri, identity, (None, None), {}, [])
        if table is None:
            return
        identity_field, datetime_field = table.identity_field(), table.datetime_field()

        bulk_count = 0
        table.set_connection_threshold(1)
        for ddict in data_dict:
            identity_value = ddict.pop(identity_field, None) if str_available(identity_field) else None
            if str_available(identity_field) and identity_value is None:
                print('Warning: identity field "' + identity_field + '" of <' + uri + '> missing.')
                continue

            datetime_value = ddict.pop(datetime_field, None) if str_available(datetime_field) else None
            if str_available(datetime_field) and datetime_value is None:
                print('Warning: datetime field "' + datetime_field + '" of <' + uri + '> missing.')
                continue

            if str_available(datetime_value):
                datetime_value = text_auto_time(datetime_value)

            extra_spec = {}
            if isinstance(self.__candidate_fields, (tuple, list)):
                for candidate_field in self.__candidate_fields:
                    candidate_value = ddict.pop(candidate_field, None)
                    if candidate_value is not None:
                        extra_spec[candidate_field] = candidate_value
                    else:
                        print('Warning: candidate field "' + candidate_field + '" of <' + uri + '> missing.')
                if None in extra_spec.values():
                    continue

            table.bulk_upsert(identity_value, datetime_value, ddict, extra_spec)
            bulk_count += 1

            if bulk_count > 5000:
                table.bulk_flush()
                bulk_count = 0

        table.bulk_flush()


# ----------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------ DataAgent Implements ------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

# ------------------- Exchange Data -------------------

class DataAgentExchangeData(DataAgent):
    def __init__(self, **kwargs):
        super(DataAgentExchangeData, self).__init__(**kwargs)

    def ref_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        nop(self, uri)
        return DataAgentUtility.a_share_market_start(), DataAgentUtility.latest_day()

    def update_list(self) -> [str]:
        nop(self)
        return DataAgentUtility.support_exchange_list()


# ------------------ Stock Common Data ------------------

class DataAgentStockData(DataAgent):
    def __init__(self, **kwargs):
        super(DataAgentStockData, self).__init__(**kwargs)

    def ref_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        nop(self, uri)
        return DataAgentUtility.stock_listing(identity), DataAgentUtility.latest_quarter()

    def update_list(self) -> [str]:
        nop(self)
        return DataAgentUtility.a_stock_list()


# ------------------ Stock Quarter Data ------------------

class DataAgentStockQuarter(DataAgent):
    def __init__(self, **kwargs):
        super(DataAgentStockQuarter, self).__init__(**kwargs)

    def data_duration(self) -> int:
        nop(self)
        return DATA_DURATION_QUARTER

    def ref_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        nop(self, uri)
        return DataAgentUtility.stock_listing(identity), DataAgentUtility.latest_quarter()

    def update_list(self) -> [str]:
        nop(self)
        return DataAgentUtility.a_stock_list()


# ------------------ Securities Daily Data ------------------

class DataAgentSecurityDaily(DataAgent):
    def __init__(self, **kwargs):
        super(DataAgentSecurityDaily, self).__init__(**kwargs)

    # ------------------------------------

    def data_duration(self) -> int:
        nop(self)
        return DATA_DURATION_DAILY

    def table_name(self, uri: str, identity: str, time_serial: tuple, extra: dict, fields: list) -> str:
        name = (uri + '_' + identity) if str_available(identity) else uri
        return name.replace('.', '_')

    def update_list(self) -> [str]:
        nop(self)
        return DataAgentUtility.a_stock_list()

    # ------------------------------------

    def query(self, uri: str, identity: str or [str], time_serial: tuple,
              extra: dict, fields: list) -> pd.DataFrame or None:
        result = None
        if not isinstance(identity, (list, tuple)):
            identity = [identity]
        for _id in identity:
            df = super(DataAgentSecurityDaily, self).query(uri, _id, time_serial, extra, fields)
            if df is None or len(df) == 0:
                continue
            result = df if result is None else pd.merge(result, df, on=self.merge_on())
        return result

    def merge(self, uri: str, identity: str, df: pd.DataFrame):
        grouped = df.groupby(df[self.identity_field()])
        for sub_identity in grouped.groups:
            sub_dataframe = grouped.get_group(sub_identity)
            super(DataAgentSecurityDaily, self).merge2(uri, sub_identity, sub_dataframe)


# ------------------ Securities In Day Data ------------------

class DataAgentSecurityInDay(DataAgentSecurityDaily):
    def __init__(self, **kwargs):
        super(DataAgentSecurityInDay, self).__init__(**kwargs)


# ---------------------- Index Daily Data ----------------------

class DataAgentIndexDaily(DataAgentSecurityDaily):
    def __init__(self, **kwargs):
        super(DataAgentIndexDaily, self).__init__(**kwargs)

    def update_list(self) -> [str]:
        nop(self)
        return DataAgentUtility.support_index_list()


# --------------------- Factor Quarter Data ---------------------

class DataAgentFactorQuarter(DataAgent):
    def __init__(self, **kwargs):
        super(DataAgentFactorQuarter, self).__init__(**kwargs)

    def adapt(self, uri: str) -> bool:
        return 'factor' in uri.lower() and 'daily' not in uri.lower()

    def update_list(self) -> [str]:
        nop(self)
        return DataAgentUtility.a_stock_list()


# # ------------------------- CSV Database -------------------------
#
# class DataAgentResult:
#     def __init__(self,
#                  uri: str, name: str,
#                  identity_field: str or None = 'Identity',
#                  datetime_field: str or None = 'DateTime',
#                  **kwargs):
#         super(DataAgentRecord, self).__init__(uri, None, name, '', identity_field, datetime_field, **kwargs)
#
#     # ---------------------------------- Constant ----------------------------------
#
#     def data_table(self, uri: str, identity: str or [str],
#                    time_serial: tuple, extra: dict, fields: list) -> ItkvTable:
#         table_name = self.table_name(uri, identity, time_serial, extra, fields)
#         return self.__database_entry.query_nosql_table(self.__depot_name, table_name,
#                                                        self.__identity_field, self.__datetime_field)
#
#     def get_field_checker(self) -> ParameterChecker:
#         return self.__checker
#
#     def config_field_checker(self, query_declare: dict, result_declare: dict):
#         if query_declare is not None or result_declare is not None:
#             self.__checker = ParameterChecker(result_declare, query_declare)
#
#     # ------------------------------- Overrideable -------------------------------
#
#     def adapt(self, uri: str) -> bool:
#         return self.__uri.lower() == uri.lower()
#
#     def data_duration(self) -> int:
#         nop(self)
#         return self.extra_param('duration', DATA_DURATION_AUTO)
#
#     def ref_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
#         nop(self, uri, identity)
#         return None, None
#
#     def data_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
#         table = self.data_table(uri, identity, (None, None), {}, [])
#         return (table.min_of(self.datetime_field(), identity), table.max_of(self.datetime_field(), identity)) \
#             if str_available(self.datetime_field()) else (None, None)
#
#     def update_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
#         local_since, local_until = self.data_range(uri, identity)
#         ref_since, ref_until = self.ref_range(uri, identity)
#         return local_until, ref_until
#
#     def merge_on(self) -> list:
#         on_column = []
#         if str_available(self.__identity_field):
#             on_column.append(self.__identity_field)
#         if str_available(self.__datetime_field):
#             on_column.append(self.__datetime_field)
#         on_column += self.extra_param('extra_key', [])
#         return on_column
#
#     def table_name(self, uri: str, identity: str or [str], time_serial: tuple, extra: dict, fields: list) -> str:
#         nop(self, identity, time_serial, extra, fields)
#         return self.table_prefix() + uri.replace('.', '_')
#
#     def update_list(self) -> [str]:
#         nop(self)
#         return []
#
#     # ------------------------------ Overrideable but -------------------------------------
#
#     def query(self, uri: str, identity: str or [str], time_serial: tuple,
#               extra: dict, fields: list) -> pd.DataFrame or None:
#         table = self.data_table(uri, identity, time_serial, extra, fields)
#         since, until = normalize_time_serial(time_serial)
#         result = table.query(identity, since, until, extra, fields)
#         df = pd.DataFrame(result)
#         return df
#
#     def merge(self, uri: str, identity: str, df: pd.DataFrame):
#         table = self.data_table(uri, identity, (None, None), {}, [])
#         identity_field, datetime_field = table.identity_field(), table.datetime_field()
#
#         table.set_connection_threshold(1)
#         for index, row in df.iterrows():
#             identity_value = None
#             if str_available(identity_field):
#                 if identity_field in list(row.index):
#                     identity_value = row[identity_field]
#             if str_available(identity_field) and identity_value is None:
#                 print('Warning: identity field "' + identity_field + '" of <' + uri + '> missing.')
#                 continue
#
#             datetime_value = None
#             if str_available(datetime_field):
#                 if datetime_field in list(row.index):
#                     datetime_value = row[datetime_field]
#                     if isinstance(datetime_value, str):
#                         datetime_value = text_auto_time(datetime_value)
#             if str_available(datetime_field) and datetime_value is None:
#                 print('Warning: datetime field "' + datetime_field + '" of <' + uri + '> missing.')
#                 continue
#             table.bulk_upsert(identity_value, datetime_value, row.dropna().to_dict())
#         table.bulk_flush()

# ----------------------------------------------------------------------------------------------------------------------

# class DataAgentFactory:
#     NO_SQL_ENTRY = None
#
#     def __init__(self):
#         pass
#
#     @staticmethod
#     def create_data_agent(uri: str, database: str, table_prefix: str,
#                           identity_field: str or None, datetime_field: str or None, **argv) -> DataAgent:
#         """
#
#         :param uri:
#         :param database:
#         :param table_prefix:
#         :param identity_field:
#         :param identity_update_list:
#         :param datetime_field:
#         :param data_since:
#         :param data_until:
#         :param data_duration:
#         :param extra_key:
#         :param key_type:
#         :param table_name:
#         :param query_split:
#         :param merge_split:
#         :param query_declare:
#         :param result_declare:
#         :param argv:
#         :return:
#         """
#
#         data_agent = DataAgent(uri, DataAgentFactory.NO_SQL_ENTRY,
#                                database, table_prefix, identity_field, datetime_field)
#
#         data_agent.identity_update_list = argv.get('identity_update_list', None)
#
#         data_agent.data_since = argv.get('data_since', None)
#         data_agent.data_until = argv.get('data_until', None)
#         data_agent.data_duration = argv.get('data_duration', None)
#
#         data_agent.extra_key = argv.get('extra_key', None)
#         data_agent.key_type = argv.get('key_type', None)
#         data_agent.table_name = argv.get('table_name', None)
#
#         data_agent.query_split = argv.get('query_split', None)
#         data_agent.merge_split = argv.get('merge_split', None)
#
#         data_agent.checker = ParameterChecker(argv.get('query_declare', None), argv.get('result_declare', None))
#
#
# DECLARE_DATA_AGENT = DataAgentFactory.create_data_agent








