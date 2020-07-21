import os
import errno

from StockAnalysisSystem.core.Utiltity.CsvRecord import *
from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem


# -------------------------------------------------- Global Functions --------------------------------------------------

def memo_path_from_user_path(user_path: str) -> str:
    memo_path = os.path.join(user_path, 'StockAnalysisSystem')
    try:
        os.makedirs(memo_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            print('Build memo path: %s FAIL' % memo_path)
    finally:
        return memo_path


def memo_path_from_project_path(project_path: str) -> str:
    memo_path = os.path.join(project_path, 'Data', 'StockMemoDeck')
    try:
        os.makedirs(memo_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            print('Build memo path: %s FAIL' % memo_path)
    finally:
        return memo_path


# ----------------------------------------------- class StockMemoRecord ------------------------------------------------

class StockMemoRecord(CsvRecord):
    ALL_COLUMNS = ['time', 'security', 'brief', 'content', 'classify']
    MUST_COLUMNS = ['time', 'security']

    def __init__(self, record_path: str):
        super(StockMemoRecord, self).__init__(record_path, StockMemoRecord.ALL_COLUMNS, StockMemoRecord.MUST_COLUMNS)

    # --------------------- Override ---------------------

    def load(self, record_path: str = '') -> bool:
        ret = super(StockMemoRecord, self).load(record_path)
        if ret:
            df = self.get_records()
            df['time'] = pd.to_datetime(df['time'], infer_datetime_format=True)
        return ret

    # ----------------------------------------------------

    def get_stock_memos(self, stock_identity: str):
        df = self.get_records({'security': stock_identity})
        return df

    def get_all_security(self) -> [str]:
        df = self.get_records()
        return list(df['security'].unique())


# class RecordSet:
#     def __init__(self, record_root: str):
#         self.__record_root = record_root
#         self.__record_depot = {}
#
#     def set_record_root(self, memo_root: str):
#         self.__record_root = memo_root
#
#     def get_record_root(self) -> str:
#         return self.__record_root
#
#     def get_record(self, record_name: str):
#         record = self.__record_depot.get(record_name, None)
#         if record is None:
#             record = Record(self.__get_record_file_path(record_name))
#             record.load()
#             self.__record_depot[record_name] = record
#         else:
#             print('Get cached record for %s' % record_name)
#         return record
#
#     def get_exists_record_name(self) -> []:
#         return self.__enumerate_record()
#
#     def __get_record_file_path(self, record_name: str) -> str:
#         return os.path.join(self.__record_root, record_name + '.csv')
#
#     def __enumerate_record(self) -> list:
#         records = []
#         for parent, dirnames, filenames in os.walk(self.__record_root):
#             for filename in filenames:
#                 if filename.endswith('.csv'):
#                     records.append(filename[:-4])
#         return records


# ------------------------------------------------ class StockMemoData -------------------------------------------------

class StockMemoData:
    RESERVED_DATA = ['root_path', 'memo_record']

    class Observer:
        def __init__(self):
            pass

        def on_data_updated(self, name: str, data: any):
            pass

    def __init__(self, sas: StockAnalysisSystem):
        self.__sas = sas

        user_path = os.path.expanduser('~')
        project_path = self.__sas.get_project_path() if self.__sas is not None else os.getcwd()

        root_path = self.__sas.get_config().get('memo_path', '')
        root_path = root_path if root_path != '' else (
            memo_path_from_project_path(project_path) if user_path == '' else
            memo_path_from_user_path(user_path))

        memo_record = StockMemoRecord(os.path.join(root_path, 'stock_memo.csv'))
        if not memo_record.load():
            print('Load stock memo fail, maybe no memo exists.')

        self.__extra_data = {
            'root_path': root_path,
            'memo_record': memo_record,
        }
        self.__observers = []

    def get_root_path(self) -> str:
        return self.__extra_data.get('root_path', '')

    def set_root_path(self, _path: str):
        self.__extra_data['root_path'] = _path
        self.broadcast_data_updated('root_path')
        self.get_memo_record().load(_path)
        self.broadcast_data_updated('memo_record')

    # -------------- Core Object --------------

    def get_sas(self) -> StockAnalysisSystem:
        return self.__sas

    def get_memo_record(self) -> StockMemoRecord:
        return self.__extra_data.get('memo_record', None)

    # ------------- Extra Object --------------

    def set_data(self, name: str, _data: any):
        if name in StockMemoData.RESERVED_DATA:
            print("Warning: You're setting reserve data.")
        self.__extra_data[name] = _data

    def get_data(self, name: str) -> any:
        return self.__extra_data.get(name, None)

    # ---------------- Update ----------------

    def add_observer(self, ob: Observer):
        self.__observers.append(ob)

    def broadcast_data_updated(self, name: str):
        for ob in self.__observers:
            ob.on_data_updated(name, self.__extra_data.get(name, None))











