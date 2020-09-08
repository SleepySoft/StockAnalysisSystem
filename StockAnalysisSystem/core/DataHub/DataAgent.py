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
    MERGE_UPSERT = 0
    MERGE_INSERT = 1

    def __init__(self,
                 uri: str, depot: DepotInterface,
                 identity_field: str or None = 'Identity',
                 datetime_field: str or None = 'DateTime',
                 merge_strategy: int = MERGE_UPSERT,
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
        self.__depot = depot
        self.__identity_field = identity_field
        self.__datetime_field = datetime_field
        self.__merge_strategy = merge_strategy
        self.__checker = None
        self.__extra = kwargs

        self.config_field_checker(kwargs.get('query_declare', None), kwargs.get('result_declare', None))

    # ---------------------------------- Constant ----------------------------------

    def base_uri(self) -> str:
        return self.__uri

    def identity_field(self) -> str or None:
        return self.__identity_field

    def datetime_field(self) -> str or None:
        return self.__datetime_field

    def extra_param(self, key: str, default: any = None) -> any:
        return self.__extra.get(key, default)

    def get_field_checker(self) -> ParameterChecker:
        return self.__checker

    def config_field_checker(self, query_declare: dict, result_declare: dict):
        if query_declare is not None or result_declare is not None:
            self.__checker = ParameterChecker(result_declare, query_declare)

    # ----------------------------- Overrideable - Properties -----------------------------

    def adapt(self, uri: str) -> bool:
        adapt = self.__extra.get('adapt')
        if isinstance(adapt, str):
            return uri == adapt
        if isinstance(adapt, (set, list, tuple)):
            return uri in adapt
        if isinstance(adapt, collections.Callable):
            return adapt(uri)
        return self.__uri.lower() == uri.lower()

    def merge_on(self) -> [str]:
        merge_on = self.__extra.get('merge_on')
        if isinstance(merge_on, str):
            return [merge_on]
        if isinstance(merge_on, (set, list, tuple)):
            return list(merge_on)
        if isinstance(merge_on, collections.Callable):
            return merge_on()
        return self.__depot.primary_keys()

    def update_list(self) -> [str]:
        update_list = self.__extra.get('update_list')
        if isinstance(update_list, str):
            return [update_list]
        if isinstance(update_list, (set, list, tuple)):
            return list(update_list)
        if isinstance(update_list, collections.Callable):
            return update_list()
        return []

    def data_duration(self) -> int:
        data_duration = self.__extra.get('data_duration', DATA_DURATION_AUTO)
        if isinstance(data_duration, collections.Callable):
            return data_duration()
        return data_duration

    def ref_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        ref_range = self.__extra.get('ref_range')
        if isinstance(ref_range, (set, list, tuple)) and len(ref_range) > 2:
            return min(ref_range[0], ref_range[1]), max(ref_range[0], ref_range[1])
        if isinstance(ref_range, collections.Callable):
            return ref_range()
        return None, None

    def update_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        local_since, local_until = self.data_range(uri, identity)
        ref_since, ref_until = self.ref_range(uri, identity)
        return local_until, ref_until

    def data_depot_of(self, uri: str = None, identity: str or [str] = None,
                      time_serial: tuple = None, extra: dict = None, fields: [str] = None) -> DepotInterface:
        nop(uri, identity, time_serial, extra, fields)
        return self.__depot

    # --------------------------------- Overrideable - RW ---------------------------------

    def query(self, uri: str, identity: str or [str], time_serial: tuple,
              extra: dict, fields: [str]) -> pd.DataFrame or None:
        conditions = self.pack_conditions(identity, time_serial)
        # TODO: Process and Remove not condition params
        conditions.update(extra)
        depot = self.data_depot_of(uri, identity, time_serial, extra, fields)
        result = depot.query(conditions=conditions, fields=fields, **extra)
        return result

    def merge(self, uri: str, identity: str, df: pd.DataFrame) -> bool:
        nop(identity)
        if not self.adapt(uri):
            return False
        return self.__depot.upsert(df) if self.__merge_strategy == DataAgent.MERGE_UPSERT else \
               self.__depot.insert(df)

    def data_range(self, uri: str, identity: str = None) -> (datetime.datetime, datetime.datetime):
        nop(uri)
        if str_available(self.datetime_field()):
            if str_available(self.identity_field()) and str_available(identity):
                return self.__depot.range_of(self.datetime_field(), conditions={self.identity_field(): identity})
            else:
                return self.__depot.range_of(self.datetime_field())
        else:
            return None, None

    # ------------------------------------ Assistance -------------------------------------

    def pack_conditions(self, identity: str or [str] = None, time_serial: datetime.datetime or tuple = None) -> dict:
        conditions = {}
        if str_available(self.__identity_field) and identity is not None:
            conditions[self.__identity_field] = identity
        if str_available(self.__datetime_field) and time_serial is not None:
            since, until = normalize_time_serial(time_serial)
            conditions[self.__datetime_field] = (since, until)
        return conditions

