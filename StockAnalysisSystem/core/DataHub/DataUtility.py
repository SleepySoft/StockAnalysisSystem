import collections
from concurrent.futures.thread import ThreadPoolExecutor

from ..Utility.common import *
from ..Utility.time_utility import *
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


# # ----------------------------------------------- IdentityNameInfoCache ------------------------------------------------
#
# class IdentityNameInfoCache:
#     def __init__(self):
#         self.__identity_info_dict = {}
#         self.__identity_name_dict = {}
#         self.__name_identity_dict = {}
#
#     # ----------------------- Sets -----------------------
#
#     def clean(self):
#         self.__identity_info_dict.clear()
#         self.__identity_name_dict.clear()
#         self.__name_identity_dict.clear()
#
#     def set_id_name(self, _id: str, name: str):
#         id_s = self.__normalize_id_name(_id)
#         name_s = self.__normalize_id_name(name)
#         self.__check_init_id_space(id_s)
#         try:
#             if name_s not in self.__identity_name_dict[id_s]:
#                 self.__identity_name_dict[id_s].append(name_s)
#             self.__name_identity_dict[name_s] = id_s
#         except Exception as e:
#             print('Error')
#         finally:
#             pass
#
#     def set_id_info(self, _id: str, key: str, val: any):
#         id_s = self.__normalize_id_name(_id)
#         key_s = self.__normalize_id_name(key)
#         self.__check_init_id_space(id_s)
#         self.__identity_info_dict[id_s][key_s] = val
#
#     # ----------------------- Gets -----------------------
#
#     def empty(self) -> bool:
#         return len(self.__identity_info_dict) == 0 and \
#                len(self.__identity_name_dict) == 0
#
#     def name_to_id(self, names: str or [str]) -> str or [str]:
#         if not isinstance(names, (list, tuple)):
#             return self.__name_identity_dict.get(self.__normalize_id_name(names),
#                                                  self.__normalize_id_name(names))
#         else:
#             return [self.__name_identity_dict.get(self.__normalize_id_name(name),
#                                                   self.__normalize_id_name(name))
#                     for name in names]
#
#     def id_to_names(self, _id: str) -> [str]:
#         id_s = self.__normalize_id_name(_id)
#         return self.__identity_name_dict.get(id_s, [''])
#
#     def get_ids(self) -> [str]:
#         return list(self.__identity_info_dict.keys())
#
#     def get_id_info(self, _id: str, keys: str or [str], default_value: any = None) -> any or [any]:
#         id_info = self.__identity_info_dict.get(self.__normalize_id_name(_id), {})
#         if not isinstance(keys, (list, tuple)):
#             return id_info.get(self.__normalize_id_name(keys), default_value)
#         else:
#             return [id_info.get(self.__normalize_id_name(key), default_value) for key in keys]
#
#     # ---------------------------------------------------------------------------------------
#
#     def __check_init_id_space(self, _id: str):
#         if _id not in self.__identity_info_dict.keys():
#             self.__identity_info_dict[_id] = {}
#             self.__identity_name_dict[_id] = []
#
#     def __normalize_id_name(self, id_or_name: str) -> str:
#         return id_or_name.strip()


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

        # TODO: What about different market
        self.__trade_calendar_cache = collections.OrderedDict()             # [(datetime.date, bool)]
        self.__trade_calendar_ready = False

    # ------------------------------- General -------------------------------

    def get_support_exchange(self) -> dict:
        return A_SHARE_MARKET

    def get_all_industries(self) -> [str]:
        agent = self.__data_center.get_data_agent('Market.SecuritiesInfo')
        depot = agent.data_depot_of('Market.SecuritiesInfo', '', None, {}, [])
        industries = depot.distinct_value_of_field('industry')
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

    # def check_update(self, uri: str, identity: str or [str] = None) -> bool:
    #     listing_date = self.get_securities_listing_date(identity, default_since())
    #     since, until = self.__data_center.calc_update_range(uri, identity)
    #     since = max(listing_date, since)
    #     if since == until:
    #         return True
    #     patch = self.__data_center.build_local_data_patch(uri, identity, (since, until))
    #     ret = self.__data_center.apply_local_data_patch(patch)
    #     return ret

    def auto_update(self, uri: str, identity: str or [str] = None,
                    time_serial: datetime.datetime or tuple or None = None,
                    full_update: bool = False, quit_flag: [bool] or None = None, progress: ProgressRate = None) -> bool:
        """
        Check last update time and auto increment update. Not support slice udpate.

        :param uri: The uri that you want to update. MUST.
        :param identity: The identity/identities that you want to update.
                         If None, function will get the update list from uri data agent.
         :param time_serial: Specify update time or time range. None for auto detecting update time range.
        :param full_update: If True, function will do full volume update
        :param quit_flag: A bool wrapped by list. If True being specified, the update will be terminated.
                          None if you don't need it.
        :param progress: The progress rate that shows the current process. None if you don't need it.
        :return: True if update successfully else False
        """
        if not str_available(uri):
            return False
        agent = self.__data_center.get_data_agent(uri)
        if agent is None:
            return False

        if quit_flag is None or len(quit_flag) == 0:
            quit_flag = [True]
        if progress is None:
            progress = ProgressRate()

        if identity is None:
            # Update whole uri, auto detect update identities
            update_list = agent.update_list()
        elif isinstance(identity, str):
            # Update specified identity
            update_list = [identity]
        elif isinstance(identity, (list, tuple, set)):
            update_list = identity
        else:
            return False
        if len(update_list) == 0:
            # Not update list, just update the uri
            update_list = [None]

        progress_count = len(update_list)
        progress.reset()
        progress.set_progress(uri, 0, progress_count)

        last_future = None
        thread_pool = ThreadPoolExecutor(max_workers=1)

        update_counter = [
            0,      # patch count
            0       # persistence count
        ]
        error_identities = []

        for identity in update_list:
            while (update_counter[0] - update_counter[1] > 20) and not quit_flag[0]:
                time.sleep(0.5)
                continue
            if quit_flag[0]:
                break

            print('------------------------------------------------------------------------------------')

            if time_serial is None:
                # Auto calculate securities update time range
                if identity is not None:
                    # Optimise: Update not earlier than listing date.
                    listing_date = self.get_securities_listing_date(identity, default_since())

                    if full_update:
                        # Full volume update
                        since, until = listing_date, now()
                    else:
                        # Increment update
                        since, until = self.__data_center.calc_update_range(uri, identity)
                        since = max(listing_date, since)
                    time_serial = (since, until)

            patch = self.__data_center.build_local_data_patch(uri, identity, time_serial, force=full_update)

            if not patch[0]:
                error_identities.append(identity)
                if len(error_identities) / len(update_list) > 0.1:
                    # More than 10% error
                    return False

            update_counter[0] += 1
            print('Patch count: %s' % update_counter[0])

            last_future = thread_pool.submit(self.__execute_persistence, uri,
                                             identity, patch, update_counter, progress)

        if last_future is not None:
            print('Waiting for persistence task finish...')
            last_future.result()

        # Update uri last update time when all update list updated.
        self.__data_center.get_update_table().update_latest_update_time(uri.split('.'))

        # since, until = agent.data_range(uri, identity) if agent is not None else (None, None)

        # ----------------------------------------------------------------
        # ---------------- Put refresh cache process here -----------------
        # ----------------------------------------------------------------

        # Refresh data utility cache if stock list or index list update
        if uri == 'Market.SecuritiesInfo':
            self.refresh_stock_cache()
        if uri == 'Market.IndexInfo':
            self.refresh_index_cache()
        if uri == 'Market.TradeCalender':
            self.refresh_trade_calendar_cache()

        if len(error_identities) != 0:
            # DEBUG: Break point here.
            print('Update complete. total count: %s, error count: %s.' % (len(update_list), len(error_identities)))
            print(str(error_identities))
        else:
            print('Update successful.')

        return True

    def __execute_persistence(self, uri: str, identity: str, patch: tuple,
                              update_counter: [int, int], progress: ProgressRate) -> bool:
        try:
            if patch is not None:
                self.__data_center.apply_local_data_patch(patch)
            if identity is not None:
                progress.set_progress([uri, identity], 1, 1)
            progress.increase_progress(uri)
        except Exception as e:
            print('Persistence error: ' + str(e))
            print(traceback.format_exc())
            return False
        finally:
            update_counter[1] += 1
            print('Persistence count: %s' % update_counter[1])
        return True

    def is_trading_day(self, _date: None or datetime.datetime or datetime.date, exchange: str = 'SSE') -> bool:
        self.__check_refresh_trade_calendar_cache()

        if _date is None:
            _date = now().date()
        elif isinstance(_date, datetime.datetime):
            _date = _date.date()
        elif isinstance(_date, datetime.date):
            pass
        else:
            print('Invalid trading day: ' + str(_date))
            return False

        with self.__lock:
            return self.__trade_calendar_cache.get(_date, False)
        
    def get_trading_days(self, since: datetime.date, until: datetime.date) -> [datetime.date]:
        trading_days = []
        since = to_date(since)
        until = to_date(until)
        with self.__lock:
            for k, v in self.__trade_calendar_cache.items():
                if since <= k <= until and v:
                    trading_days.append(k)
        return trading_days

    # def get_last_trading_day(self, exchange='SSE') -> datetime.datetime:
    #     trade_calender = self.__data_center.query('Market.TradeCalender', exchange=exchange,
    #                                               trade_date=(days_ago(365), now()), status=1)
    #     trade_calender = trade_calender[trade_calender['status'] == 1]
    #     trade_calender = trade_calender.sort('trade_date')
    #     return trade_calender[0]['trade_date']

    # -------------------------------- Guess --------------------------------

    def guess_securities(self, text: str) -> [str]:
        """
        Guess securities by parts of text. Match in following orders:
        1.Security name
        2.Security code (only if the text len >= 3)
        :param text:
        :return:
        """
        match_result = self.__guess_text_in_list(list(self.__stock_name_id.keys()), text)
        result = [self.__stock_name_id.get(k) for k in match_result]

        # if text.isdigit() and len(text) >= 3:
        match_result = self.__guess_text_in_list(list(self.__stock_id_name.keys()), text)
        result.extend(match_result)

        return list(set(result))

    @staticmethod
    def __guess_text_in_list(text_list: list, text: str) -> [str]:
        result = []
        for t in text_list:
            if text in t:
                result.append(t)
        return result

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

    def names_to_stock_identity(self, names: str or [str]) -> str or [str]:
        self.__check_refresh_stock_cache()
        if isinstance(names, list):
            return [self.__stock_name_id.get(name, name) for name in names]
        else:
            return self.__stock_name_id.get(names, names)

    def stock_identity_to_name(self, stock_identities: str or [str]) -> str or [str]:
        self.__check_refresh_stock_cache()
        if isinstance(stock_identities, list):
            return [self.__stock_id_name.get(stock_identity, stock_identity) for stock_identity in stock_identities]
        else:
            return self.__stock_id_name.get(stock_identities, stock_identities)

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
        with self.__lock:
            self.__refresh_stock_cache()
            self.__refresh_index_cache()
            self.__refresh_trade_calendar_cache()

    def refresh_stock_cache(self):
        with self.__lock:
            self.__refresh_stock_cache()

    def refresh_index_cache(self):
        with self.__lock:
            self.__refresh_index_cache()

    def refresh_trade_calendar_cache(self):
        with self.__lock:
            self.__refresh_trade_calendar_cache()

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

    # --------------------- Trade Calendar ---------------------

    def __check_refresh_trade_calendar_cache(self):
        if not self.__trade_calendar_ready:
            self.__lock.acquire()
            if not self.__trade_calendar_ready:
                self.__refresh_trade_calendar_cache()
            self.__lock.release()

    def __refresh_trade_calendar_cache(self):
        df = self.__data_center.query('Market.TradeCalender')
        try:
            self.__trade_calendar_cache.clear()
            for _time, _open in zip(df['trade_date'], df['status']):
                _date = _time.date()
                self.__trade_calendar_cache[_date] = (_open != 0)
        except Exception as e:
            print('Build trace calendar cache error: ' + str(e))
            print(traceback.format_exc())
        finally:
            pass

    # --------------------------------------- Assistance ---------------------------------------

    def __query_identity_filed_value(self, uri: str, identity: str, field: str, default_val: any) -> any:
        result = self.__data_center.query(uri, identity, fields=[field])
        if result is None or len(result) == 0 or field not in result.columns:
            return default_val
        else:
            ret = result[field][0]
            return ret











