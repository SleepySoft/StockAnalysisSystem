import os
import errno

from StockAnalysisSystem.core.Utiltity.CsvRecord import *
from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.append(root_path)


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
        return df['security'].unique()


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
    def __init__(self, sas: StockAnalysisSystem):
        self.__sas = sas
        self.__extra_data = {}

        user_path = os.path.expanduser('~')
        project_path = self.__sas.get_project_path() if self.__sas is not None else os.getcwd()

        memo_path = self.__sas.get_config().get('memo_path', '')
        memo_path = memo_path if memo_path != '' else (
            memo_path_from_project_path(project_path) if user_path == '' else
            memo_path_from_user_path(user_path))

        self.__root_path = memo_path
        self.__memo_record = StockMemoRecord(os.path.join(self.__root_path, 'stock_memo.csv'))
        if not self.__memo_record.load():
            print('Load stock memo fail, maybe no memo exists.')

    def get_root_path(self) -> str:
        return self.__root_path

    def set_root_path(self, _path: str):
        self.__root_path = _path

    # -------------- Core Object --------------

    def get_sas(self) -> StockAnalysisSystem:
        return self.__sas

    def get_memo_record(self) -> StockMemoRecord:
        return self.__memo_record

    # ------------- Extra Object --------------

    def set_data(self, name: str, _data: any):
        self.__extra_data[name] = _data

    def get_data(self, name: str) -> any:
        return self.__extra_data.get(name, None)











