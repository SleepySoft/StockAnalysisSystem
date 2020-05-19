from ..Utiltity.common import *
from ..Utiltity.time_utility import *
from .UniversalDataCenter import UniversalDataCenter


A_SHARE_MARKET = collections.OrderedDict([
    ('SSE', '上海证券交易所'),
    ('SZSE', '深圳证券交易所'),
])
ALL_SHARE_MARKET = ['SSE', 'SZSE', 'CSI', 'CICC', 'SW', 'MSCI', 'OTH']

# Too much indexes (more than 9000)
# Hard coded. Select form TestData/Market_IndexInfo.csv
# TODO: Configurable

SUPPORT_INDEX = collections.OrderedDict([
    ('000001.SSE', '上证综指'),
    ('000002.SSE', '上证A指'),
    ('000003.SSE', '上证B指'),
    ('000016.SSE', '上证50'),
    ('399001.SESZ', '深证成指'),
    ('399005.SESZ', '中小板指'),
    ('399006.SESZ', '创业板指'),
])


# def csv_name_column_to_identity(csv_file: str, column: str) -> bool:
#     df = pd.read_csv(csv_file, index_col=None)
#     if column not in list(df.columns):
#         return False
#     from stock_analysis_system import StockAnalysisSystem
#     data_utility = StockAnalysisSystem().get_data_hub_entry().get_data_utility()
#     name_column = df[column].values.tolist()
#     id_column = data_utility.names_to_stock_identity(name_column)
#     df[column] = np.array(id_column)
#     df.to_csv(csv_file + '_parsed.csv')


# ----------------------------------------------- IdentityNameInfoCache ------------------------------------------------

class IdentityNameInfoCache:
    def __init__(self):
        self.__identity_info_dict = {}
        self.__identity_name_dict = {}
        self.__name_identity_dict = {}

    # ----------------------- Sets -----------------------

    def clean(self):
        self.__identity_info_dict.clear()
        self.__identity_name_dict.clear()
        self.__name_identity_dict.clear()

    def set_id_name(self, _id: str, name: str):
        id_s = self.__normalize_id_name(_id)
        name_s = self.__normalize_id_name(name)
        self.__check_init_id_space(id_s)
        try:
            if name_s not in self.__identity_name_dict[id_s]:
                self.__identity_name_dict[id_s].append(name_s)
            self.__name_identity_dict[name_s] = id_s
        except Exception as e:
            print('Error')
        finally:
            pass

    def set_id_info(self, _id: str, key: str, val: any):
        id_s = self.__normalize_id_name(_id)
        key_s = self.__normalize_id_name(key)
        self.__check_init_id_space(id_s)
        self.__identity_info_dict[id_s][key_s] = val

    # ----------------------- Gets -----------------------

    def empty(self) -> bool:
        return len(self.__identity_info_dict) == 0 and \
               len(self.__identity_name_dict) == 0

    def name_to_id(self, names: str or [str]) -> str or [str]:
        if not isinstance(names, (list, tuple)):
            return self.__identity_name_dict.get(self.__normalize_id_name(names),
                                                 self.__normalize_id_name(names))
        else:
            return [self.__identity_name_dict.get(self.__normalize_id_name(name),
                                                  self.__normalize_id_name(name))
                    for name in names]

    def id_to_names(self, _id: str) -> [str]:
        id_s = self.__normalize_id_name(_id)
        return self.__identity_name_dict.get(id_s, [''])

    def get_ids(self) -> [str]:
        return list(self.__identity_info_dict.keys())

    def get_id_info(self, _id: str, keys: str or [str], default_value: any=None) -> any or [any]:
        id_info = self.__identity_info_dict.get(self.__normalize_id_name(_id), {})
        if not isinstance(keys, (list, tuple)):
            return id_info.get(self.__normalize_id_name(keys), default_value)
        else:
            return [id_info.get(self.__normalize_id_name(key), default_value) for key in keys]

    # ---------------------------------------------------------------------------------------

    def __check_init_id_space(self, _id: str):
        if _id not in self.__identity_info_dict.keys():
            self.__identity_info_dict[_id] = {}
            self.__identity_name_dict[_id] = []

    def __normalize_id_name(self, id_or_name: str) -> str:
        return id_or_name.strip()


# ---------------------------------------------------- DataUtility -----------------------------------------------------

class DataUtility:
    def __init__(self, data_center: UniversalDataCenter):
        self.__data_center = data_center
        self.__lock = threading.Lock()

        self.__stock_id_name = {}
        self.__stock_name_id = {}
        self.__stock_cache_ready = False
        # self.__stock_cache = IdentityNameInfoCache()

        self.__index_id_name = {}
        self.__index_name_id = {}
        self.__index_cache_ready = False
        # self.__index_cache = IdentityNameInfoCache()

    # ------------------------------- General -------------------------------

    def get_support_exchange(self) -> dict:
        return A_SHARE_MARKET

    def get_all_industries(self) -> [str]:
        agent = self.__data_center.get_data_agent('Market.SecuritiesInfo')
        itkv_table = agent.data_table('Market.SecuritiesInfo', '', None, {}, [])
        industries = itkv_table.get_distinct_values('industry')
        return industries

    def get_industry_stocks(self, industry: str) -> [str]:
        result = self.__data_center.query('Market.SecuritiesInfo', '', fields=['stock_identity'], industry=industry)
        if result is None or len(result) == 0 or 'stock_identity' not in result.columns:
            return []
        else:
            ret = result['stock_identity'].tolist()
            return ret

    def get_securities_listing_date(self, securities: str, default_val: datetime.datetime) -> datetime.datetime:
        return self.get_stock_listing_date(securities, default_val) if securities in self.__stock_id_name.keys() else \
               self.get_index_listing_date(securities, default_val)

    # -------------------------------- Stock --------------------------------

    def stock_cache_ready(self) -> bool:
        return self.__stock_cache_ready

    def get_stock_list(self) -> [(str, str)]:
        self.__check_refresh_stock_cache()
        ret = [(key, value) for key, value in self.__stock_id_name.items()]
        return ret

    def get_stock_identities(self) -> [str]:
        self.__check_refresh_stock_cache()
        ret = list(self.__stock_id_name.keys())
        return ret

    def names_to_stock_identity(self, names: [str]) -> [str]:
        self.__check_refresh_stock_cache()
        ret = [self.__stock_name_id.get(name, name) for name in names]
        return ret

    def get_stock_industry(self, stock_identity: str, default_val: str = '') -> str:
        return self.__query_identity_filed_value('Market.SecuritiesInfo', stock_identity, 'industry', default_val)

    def get_stock_listing_date(self, stock_identity: str, default_val: datetime.datetime) -> datetime.datetime:
        return self.__query_identity_filed_value('Market.SecuritiesInfo', stock_identity, 'listing_date', default_val)

    # --------------------------------------- Index ---------------------------------------

    def index_cache_ready(self) -> bool:
        return self.__index_cache_ready

    def get_index_list(self) -> [(str, str)]:
        self.__check_refresh_index_cache()
        ret = [(key, value) for key, value in self.__index_id_name.items()]
        return ret

    def get_index_identities(self) -> [str]:
        self.__check_refresh_index_cache()
        ret = list(self.__index_id_name.keys())
        return ret

    def get_support_index(self) -> dict:
        return SUPPORT_INDEX

    def get_index_category(self, index_identity: str, default_val: str = '') -> str:
        return self.__query_identity_filed_value('Market.IndexInfo', index_identity, 'category', default_val)

    def get_index_listing_date(self, index_identity: str, default_val: datetime.datetime) -> datetime.datetime:
        return self.__query_identity_filed_value('Market.IndexInfo', index_identity, 'listing_date', default_val)

    # --------------------------------------- Query ---------------------------------------

    def auto_query(self, identity: str or [str], time_serial: tuple, fields: [str],
                   join_on: [str] = None) -> pd.DataFrame or [pd.DataFrame]:
        group = self.__data_center.readable_to_uri(fields)
        if 'None' in group.keys():
            print('Warning: Unknown fields in auto_query() : ' + str(group['None']))
            del group['None']
        result = None
        for uri, fields in group.items():
            if join_on is not None:
                fields.extend(join_on)
                fields = list(set(fields))
            df = self.__data_center.query(uri, identity, time_serial, fields=fields, readable=True)
            if join_on is not None:
                result = df if result is None else pd.merge(result, df, how='left', on=join_on)
            else:
                result = [] if result is None else result
                result.append(df)
        return result

    def query_daily_trade_data(self, identity: str, time_serial: tuple = (default_since(), now()),
                               _open: bool = True, _close: bool = True, high: bool = True, low: bool = True,
                               amount: bool = True) -> pd.DataFrame or None:
        fields = [
            'open' if _open else '',
            'close' if _close else '',
            'high' if high else '',
            'low' if low else '',
            'amount' if amount else '',
        ]
        fields.remove('')
        if len(fields) == 0:
            return None
        df = self.__data_center.query('TradeData.Stock.Daily', identity, time_serial, fields=fields)
        return df

    # ------------------------------------------------- Refresh Cache --------------------------------------------------

    # --------------------------- All ---------------------------

    def refresh_cache(self):
        self.__lock.acquire()
        self.__refresh_stock_cache()
        self.__refresh_index_cache()
        self.__lock.release()

    # -------------------------- Stock --------------------------

    def __check_refresh_stock_cache(self):
        if not self.__stock_cache_ready:
            self.__lock.acquire()
            if not self.__stock_cache_ready:
                self.__refresh_stock_cache()
            self.__lock.release()

    def __refresh_stock_cache(self):
        clock = Clock()
        df = self.__data_center.query('Market.SecuritiesInfo')
        print('Query stock info time spending: %sms' % clock.elapsed_ms())
        
        if df is None or len(df) == 0 or 'stock_identity' not in df.columns or 'name' not in df.columns:
            print('No stock information. Please Update Market.SecuritiesInfo first.')
            return

        clock.reset()
        id_name_dict = dict(zip(df.stock_identity, df.name))
        print('Build stock identity name mapping time spending: %sms' % clock.elapsed_ms())

        clock.reset()
        name_id_dict = dict(zip(df.name, df.stock_identity))
        print('Build stock name identity mapping time spending: %sms' % clock.elapsed_ms())

        clock.reset()
        df = self.__data_center.query('Market.NamingHistory', fields=['stock_identity', 'name'])
        his_name_id_dict = dict(zip(df.name, df.stock_identity))
        print('Build stock history name identity mapping time spending: %sms' % clock.elapsed_ms())

        clock.reset()
        name_id_dict.update(his_name_id_dict)
        print('Merge stock name identity mapping time spending: %sms' % clock.elapsed_ms())

        # Assignment at last to make access lock free
        self.__stock_id_name = id_name_dict
        self.__stock_name_id = name_id_dict
        self.__stock_cache_ready = True

    # -------------------------- Index --------------------------

    def __check_refresh_index_cache(self):
        if not self.__index_cache_ready:
            self.__lock.acquire()
            if not self.__index_cache_ready:
                self.__refresh_index_cache()
            self.__lock.release()

    def __refresh_index_cache(self):
        clock = Clock()
        df = self.__data_center.query('Market.IndexInfo')
        print('Query index info time spending: %sms' % clock.elapsed_ms())

        if df is None or len(df) == 0 or 'index_identity' not in df.columns or 'name' not in df.columns:
            print('No stock information. Please Update Market.IndexInfo first.')
            return

        clock.reset()
        id_name_dict = dict(zip(df.index_identity, df.name))
        print('Build index name identity mapping time spending: %sms' % clock.elapsed_ms())

        clock.reset()
        name_id_dict = dict(zip(df.name, df.index_identity))
        print('Build index name identity mapping time spending: %sms' % clock.elapsed_ms())

        # Assignment at last to make access lock free
        self.__index_id_name = id_name_dict
        self.__index_name_id = name_id_dict
        self.__index_cache_ready = True

    # --------------------------------------- Assistance ---------------------------------------

    def __query_identity_filed_value(self, uri: str, identity: str, field: str, default_val: any) -> any:
        result = self.__data_center.query(uri, identity, fields=[field])
        if result is None or len(result) == 0 or field not in result.columns:
            return default_val
        else:
            ret = result[field][0]
            return ret











