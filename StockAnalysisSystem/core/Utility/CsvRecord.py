import pandas as pd
from .df_utility import *


class CsvRecord:
    def __init__(self, record_path: str, record_columns: [str], must_columns: [str] or None = None):
        self.__record_path = record_path
        self.__record_columns = record_columns
        self.__must_columns = must_columns
        self.__record_sheet = pd.DataFrame(columns=self.__record_columns)

    def columns(self) -> [str]:
        return self.__record_columns

    def is_empty(self) -> bool:
        return self.__record_sheet is None or self.__record_sheet.empty

    def add_record(self, _data: dict, _save: bool = True) -> (bool, int):
        if not self.__check_must_columns(_data, True, True):
            return False, -1
        df = self.__record_sheet
        max_index = max(df.index) if len(df) > 0 else 0
        new_index = max_index + 1
        row = [_data.get(k, '') for k in self.__record_columns]
        df.loc[new_index, self.__record_columns] = tuple(row)
        return (self.save() if _save else True), new_index

    def update_record(self, index, _data: dict, _save: bool = True) -> bool:
        if not self.__check_must_columns(_data, False, True):
            return False
        fields = list(_data.keys())
        values = [_data.get(field, '') for field in fields]
        df = self.__record_sheet
        if index in df.index.values:
            df.loc[index, fields] = tuple(values)
        else:
            print('Warning: Index %s not in record.' % str(index))
            return False
        return self.save() if _save else True

    def get_records(self, conditions: dict or None = None) -> pd.DataFrame:
        if conditions is None or len(conditions) == 0:
            return self.__record_sheet
        df = self.__record_sheet
        # https://stackoverflow.com/a/40125748/12929244
        mask = pd.concat([df[k].eq(v) for k, v in conditions.items()], axis=1).all(axis=1)
        return df[mask]
        # return df[np.logical_and.reduce([df[k] == v for k, v in conditions.items()])]

    def del_records(self, idx: int or [int]):
        self.__record_sheet = self.__record_sheet.drop(idx)

    def load(self, record_path: str = '') -> bool:
        if record_path != '':
            if self.__load(record_path):
                self.__record_path = record_path
                return True
            else:
                return False
        return self.__load(self.__record_path)

    def save(self, record_path: str = ''):
        if record_path != '':
            if self.__save(record_path):
                self.__record_path = record_path
                return True
            else:
                return False
        return self.__save(self.__record_path)

    # ---------------------------------------------------

    def __load(self, record_path: str) -> bool:
        try:
            df = pd.read_csv(record_path)
            # df['time'] = pd.to_datetime(df['time'], infer_datetime_format=True)
            df.reindex()
            self.__record_sheet = df
            return column_includes(self.__record_sheet.columns, self.__record_columns)
        except Exception as e:
            return False
        finally:
            pass

    def __save(self, record_path: str) -> bool:
        try:
            self.__record_sheet = self.__record_sheet[self.__record_columns]
            self.__record_sheet.to_csv(record_path)
            return True
        except Exception as e:
            print('Save stock memo %s error.' % record_path)
            print(e)
            return False
        finally:
            pass

    def __check_must_columns(self, _data: dict, check_exists: bool, check_empty: bool) -> bool:
        if self.__must_columns is None or len(self.__must_columns) == 0:
            return True
        for must_column in self.__must_columns:
            if must_column not in _data.keys():
                if check_exists:
                    return False
            else:
                _value = _data.get(must_column)
                if check_empty and (_value is None or _value == ''):
                    return False
        return True



















