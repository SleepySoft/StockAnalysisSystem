import logging
import threading
import numpy as np
import pandas as pd
from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    import Utiltity.common as common
    from Utiltity.time_utility import *
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
    from DataHub.UniversalDataCenter import ParameterChecker
    from DataHub.UniversalDataCenter import UniversalDataTable
    from DataHub.UniversalDataCenter import UniversalDataCenter
except Exception as e:
    sys.path.append(root_path)

    import Utiltity.common as common
    from Utiltity.time_utility import *
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
    from DataHub.UniversalDataCenter import ParameterChecker
    from DataHub.UniversalDataCenter import UniversalDataTable
    from DataHub.UniversalDataCenter import UniversalDataCenter
finally:
    logger = logging.getLogger('')


def csv_name_column_to_identity(csv_file: str, column: str) -> bool:
    df = pd.read_csv(csv_file, index_col=None)
    if column not in list(df.columns):
        return False
    from stock_analysis_system import StockAnalysisSystem
    data_utility = StockAnalysisSystem().get_data_hub_entry().get_data_utility()
    name_column = df[column].values.tolist()
    id_column = data_utility.names_to_stock_identity(name_column)
    df[column] = np.array(id_column)
    df.to_csv(csv_file + '_parsed.csv')


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

        self.__stock_cache_ready = False
        self.__stock_cache = IdentityNameInfoCache()

        self.__index_cache_ready = False
        self.__index_cache = IdentityNameInfoCache()

    # ------------------------------- General -------------------------------

    def get_securities_listing_date(self, securities: str, default_val: datetime.datetime) -> datetime.datetime:
        return self.get_stock_listing_date(securities, self.get_index_listing_date(securities, default_val))

    # -------------------------------- Stock --------------------------------

    def stock_cache_ready(self) -> bool:
        return self.__stock_cache_ready

    def get_stock_list(self) -> [(str, str)]:
        self.__lock.acquire()
        if not self.__stock_cache_ready:
            self.__refresh_stock_cache()
        ids = self.__stock_cache.get_ids()
        ret = [(_id, self.__stock_cache.id_to_names(_id)[0]) for _id in ids]
        self.__lock.release()
        return ret

    def get_stock_identities(self) -> [str]:
        self.__lock.acquire()
        if not self.__stock_cache_ready:
            self.__refresh_stock_cache()
        ids = self.__stock_cache.get_ids()
        self.__lock.release()
        return ids

    def names_to_stock_identity(self, names: [str]) -> [str]:
        self.__lock.acquire()
        if not self.__stock_cache_ready:
            self.__refresh_stock_cache()
        ids = self.__stock_cache.name_to_id(names)
        self.__lock.release()
        return ids

    def get_stock_listing_date(self, stock_identity: str, default_val: datetime.datetime) -> datetime.datetime:
        self.__lock.acquire()
        if not self.__stock_cache_ready:
            self.__refresh_stock_cache()
        ret = self.__stock_cache.get_id_info(stock_identity, 'listing_date', default_val)
        self.__lock.release()
        return ret

    # --------------------------------------- Index ---------------------------------------

    def index_cache_ready(self) -> bool:
        return self.__index_cache_ready

    def get_index_list(self) -> [(str, str)]:
        self.__lock.acquire()
        if not self.__index_cache_ready:
            self.__refresh_index_cache()
        ids = self.__index_cache.get_ids()
        ret = [(_id, self.__index_cache.id_to_names(_id)[0]) for _id in ids]
        self.__lock.release()
        return ret

    def get_index_identities(self) -> [str]:
        self.__lock.acquire()
        if not self.__index_cache_ready:
            self.__refresh_index_cache()
        ids = self.__index_cache.get_ids()
        self.__lock.release()
        return ids

    def get_index_listing_date(self, index_identity: str, default_val: datetime.datetime) -> datetime.datetime:
        self.__lock.acquire()
        if not self.__index_cache_ready:
            self.__refresh_index_cache()
        ret = self.__index_cache.get_id_info(index_identity, 'listing_date', default_val)
        self.__lock.release()
        return ret

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

    # -------------------------------------- Refresh --------------------------------------

    def refresh_cache(self):
        self.__lock.acquire()
        self.__refresh_stock_cache()
        self.__refresh_index_cache()
        self.__lock.release()
        self.__stock_cache_ready = True

    # ------------------------------------------------------------------------------------------------------------------

    def __refresh_stock_cache(self):
        securities_info = self.__data_center.query('Market.SecuritiesInfo',
                                                   fields=['stock_identity', 'name', 'listing_date'])
        if securities_info is not None:
            for index, row in securities_info.iterrows():
                self.__stock_cache.set_id_name(row['stock_identity'], row['name'])
                self.__stock_cache.set_id_info(row['stock_identity'], 'listing_date', row['listing_date'])

        securities_used_name = self.__data_center.query('Market.NamingHistory',
                                                        fields=['stock_identity', 'name', 'naming_date'])
        for index, row in securities_used_name.iterrows():
            self.__stock_cache.set_id_name(row['stock_identity'], row['name'].lower().replace('*', ''))

    def __refresh_index_cache(self):
        index_info = self.__data_center.query('Market.IndexInfo',
                                              fields=['index_identity', 'name', 'listing_date'])
        for index, row in index_info.iterrows():
            self.__index_cache.set_id_name(row['index_identity'], row['name'])
            self.__index_cache.set_id_info(row['index_identity'], 'listing_date', row['listing_date'])
        self.__index_cache_ready = True


# ----------------------------------------------------------------------------------------------------------------------
#                                                         Test
# ----------------------------------------------------------------------------------------------------------------------

def test_identity_name_info_cache():
    cache = IdentityNameInfoCache()

    cache.set_id_name('id_1', 'id_1_name_1')
    cache.set_id_name('id_1', 'id_1_name_1')
    cache.set_id_name('id_1', 'id_1_name_2')
    cache.set_id_name('id_1', 'id_1_name_3')
    cache.set_id_info('id_1', 'date', datetime.date(1990, 1, 1))
    cache.set_id_info('id_1', 'date', datetime.date(2000, 2, 2))
    cache.set_id_info('id_1', 'key1', 'value1')
    cache.set_id_info('id_1', 'key2', 'value2')
    cache.set_id_info('id_1', 'key3', 'value3')

    cache.set_id_name('id_2', 'id_2_name_1')
    cache.set_id_name('id_2', 'id_2_name_2')
    cache.set_id_name('id_2', 'id_2_name_3')
    cache.set_id_info('id_2', 'date', datetime.date(2010, 10, 10))

    # ---------------- Test Ids -----------------

    assert 'id_1' in cache.get_ids()
    assert 'id_2' in cache.get_ids()

    # ---------------- Test name ----------------

    # No duplicate names
    id_1_names = cache.id_to_names('id_1')
    assert len(id_1_names) == 3
    assert 'id_1_name_1' in id_1_names
    assert 'id_1_name_2' in id_1_names
    assert 'id_1_name_3' in id_1_names

    # Normal case
    id_2_names = cache.id_to_names('id_2')
    assert len(id_2_names) == 3

    # If id not exits, returns ['']
    id_3_names = cache.id_to_names('id_3')
    assert len(id_3_names) == 1
    assert id_3_names[0] == ''

    # ---------------- Test Info ----------------

    # Should keep the last set info
    assert cache.get_id_info('id_1', 'date') == datetime.date(2000, 2, 2)

    # Should keep the order of query keys
    # Return default value if info not exists
    info = cache.get_id_info('id_1', ['key3', 'key_x', 'key1', 'key2'], 'NotExists')
    assert info[0] == 'value3'
    assert info[1] == 'NotExists'
    assert info[2] == 'value1'
    assert info[3] == 'value2'


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    test_identity_name_info_cache()

    # If program reaches here, all test passed.
    print('All test passed.')


# ------------------------------------------------- Exception Handling -------------------------------------------------

def exception_hook(type, value, tback):
    # log the exception here
    print('Exception hook triggered.')
    print(type)
    print(value)
    print(tback)
    # then call the default handler
    sys.__excepthook__(type, value, tback)


if __name__ == "__main__":
    sys.excepthook = exception_hook
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass









