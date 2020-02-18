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


class DataUtility:
    def __init__(self, data_center: UniversalDataCenter):
        self.__data_center = data_center
        self.__lock = threading.Lock()

        self.__stock_id_information_table = {}
        self.__stock_history_name_id_table = {}

    def get_stock_list(self) -> [(str, str)]:
        self.__lock.acquire()
        if len(self.__stock_id_information_table) == 0:
            self.__refresh_securities_cache()
        ret = [(_id, _info[0]) for _id, _info in self.__stock_id_information_table.items()]
        self.__lock.release()
        return ret

    def get_stock_identities(self) -> [str]:
        self.__lock.acquire()
        if len(self.__stock_id_information_table) == 0:
            self.__refresh_securities_cache()
        ret = [_id for _id, _info in self.__stock_id_information_table.items()]
        self.__lock.release()
        return ret

    def names_to_stock_identity(self, names: [str]) -> [str]:
        self.__lock.acquire()
        if len(self.__stock_id_information_table) == 0:
            self.__refresh_securities_cache()
        if not isinstance(names, list):
            names = [str(names)]

        # The result is a tuple like (stock_identity, naming_date)
        # We'll keep the original name if there's no match record.
        # Too simple: [self.__stock_history_name_id_table.get(name, (name, ''))[0] for name in names]

        ids = []
        for name in names:
            _id = self.__stock_history_name_id_table.get(name.lower(), ('', ''))[0]
            if _id != '':
                ids.append(_id)
            else:
                # For debug
                ids.append(name)
        self.__lock.release()

        return ids

    def get_stock_listing_date(self, stock_identity: str, default_val: datetime.datetime) -> datetime.datetime:
        self.__lock.acquire()
        ret = self.__stock_id_information_table[stock_identity][1] \
            if stock_identity in self.__stock_id_information_table.keys() else default_val
        self.__lock.release()
        return ret

    def refresh_securities_cache(self):
        self.__refresh_securities_cache()

    # ------------------------------------------------------------------------------------------------------------------

    def __refresh_securities_cache(self):
        securities_info = self.__data_center.query('Market.SecuritiesInfo',
                                                   fields=['stock_identity', 'name', 'listing_date'])
        if securities_info is not None:
            self.__stock_id_information_table = {row['stock_identity']: (row['name'], row['listing_date'])
                                                 for index, row in securities_info.iterrows()}

        securities_used_name = self.__data_center.query('Market.NamingHistory',
                                                        fields=['stock_identity', 'name', 'naming_date'])
        if securities_used_name is not None:
            self.__stock_history_name_id_table = {
                # Convert to lower case and remove * mark for easy indexing.
                row['name'].lower().replace('*', ''): (row['stock_identity'],
                                                       row['naming_date'])
                for index, row in securities_used_name.iterrows()}

            # Also add current name into history naming list
            if securities_info is not None:
                for key, info in self.__stock_id_information_table.items():
                    trimed_name = info[0].lower().replace('*', '')
                    if trimed_name not in self.__stock_history_name_id_table.keys():
                        self.__stock_history_name_id_table[trimed_name] = (key, today())























