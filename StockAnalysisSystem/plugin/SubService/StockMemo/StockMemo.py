import os
import errno
import datetime
import pandas as pd
from StockAnalysisSystem.core.Utility.CsvRecord import CsvRecord


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


# -------------------------------------------------- class StockMemo ---------------------------------------------------

class StockMemo:
    def __init__(self, memo_path: str):
        self.__memo_record: StockMemoRecord = None
        if memo_path is not None and memo_path != '':
            self.stock_memo_set_path(memo_path)

    def raw_record(self) -> StockMemoRecord:
        return self.__memo_record

    def stock_memo_save(self) -> bool:
        return self.__memo_record.save()

    def stock_memo_load(self) -> bool:
        return self.__memo_record.load()

    def stock_memo_set_path(self, memo_path: str):
        self.__memo_record = StockMemoRecord(memo_path)
        if not self.__memo_record.load():
            print('Load stock memo fail, maybe no memo exists.')

    def stock_memo_get_record(self, security: str) -> pd.DataFrame:
        return self.__memo_record.get_stock_memos(security)

    def stock_memo_add_record(self, security: str, _time: datetime,
                              brief: str, content: str, _save: bool = True) -> (bool, int):
        ret, index = self.__memo_record.add_record({
            'time': _time,
            'security': security,
            'brief': brief,
            'content': content,
            'classify': 'memo',
        }, _save)
        return ret, index

    def stock_memo_update_record(self, index: int, security: str, _time: datetime,
                                 brief: str, content: str, _save: bool = True) -> bool:
        ret = self.__memo_record.update_record(index, {
            'time': _time,
            'security': security,
            'brief': brief,
            'content': content,
            'classify': 'memo',
        }, _save)
        return ret

    def stock_memo_delete_record(self, indexes: int or [int], _save: bool = True) -> bool:
        indexes = list(indexes) if isinstance(indexes, (list, tuple, set)) else [indexes]
        for index in indexes:
            self.__memo_record.del_records(index)
        return self.__memo_record.save() if _save else True

    def get_stock_memo_all_security(self) -> [str]:
        return self.__memo_record.get_all_security()



