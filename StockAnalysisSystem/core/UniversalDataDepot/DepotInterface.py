import pandas as pd


class Result:
    E_FAIL = 0
    E_SUCCESSFUL = 1
    E_NOT_SUGGEST = 2
    E_NOT_SUPPORT = -1
    E_NOT_IMPLEMENT = -2
    E_NOT_FULL_SUPPORT = -3

    def __init__(self, return_data: any, return_code: int = E_SUCCESSFUL, return_text: str = ''):
        self.__return_data = return_data
        self.__return_code = return_code
        self.__return_text = return_text

    def data(self) -> any:
        return self.__return_data

    def code(self) -> int:
        return self.__return_code

    def text(self) -> str:
        return self.__return_text

    def error(self) -> bool:
        return self.__return_code <= 0


class DepotInterface:
    def __init__(self, primary_keys: [str]):
        if isinstance(primary_keys, (list, tuple, set)):
            self.__primary_keys = list(primary_keys)
        elif isinstance(primary_keys, str):
            self.__primary_keys = [primary_keys]
        else:
            self.__primary_keys = primary_keys

    # ------------------------------- Basic Operation -------------------------------

    def query(self, *args, conditions: dict = None, fields: [str] or None = None, **kwargs) -> pd.DataFrame or None:
        """
        Query data by conditions. Condition rules:
            tuple: range condition
                (lower, upper) - Find the item that between or equal to the lower and upper value
                (lower, None) - Find the item that larger or equal to the lower value
                (None, upper) - Find the item that less or equal to the upper value
            list: in list condition
            others: equal condition
        :param args: The args default meets the sequence of primary keys
        :param conditions: The conditions as dict - {field: condition}
        :param fields: Query fields
        :param kwargs: Specify other conditions by key: value
        :return: Default as DataFrame
        """
        pass

    def insert(self, dataset: pd.DataFrame or dict or any) -> bool:
        pass

    def upsert(self, dataset: pd.DataFrame or dict or any) -> bool:
        pass

    def delete(self, *args, conditions: dict = None, fields: [str] or None = None,
               delete_all: bool = False, **kwargs) -> bool:
        pass

    def drop(self) -> bool:
        pass

    # ----------------------------- Advanced Operation ------------------------------

    def range_of(self, field, *args, conditions: dict = None, **kwargs) -> (any, any):
        pass

    def record_count(self) -> int:
        pass

    def distinct_value_of_field(self, field: str) -> [str]:
        pass

    def all_fields(self) -> [str]:
        pass

    def remove_field(self, key: str) -> bool:
        pass

    def rename_field(self, field_old: str, field_new: str) -> bool:
        pass

    # --------------------------------- Assistance ----------------------------------

    def log(self, *args):
        print(*args)

    def primary_keys(self) -> [str]:
        return self.__primary_keys

    def full_conditions(self, *args, conditions) -> dict:
        full_conditions = {}
        for index, arg in enumerate(args):
            if index >= len(self.__primary_keys):
                print('Warning: Args longer than primary keys. Ignore.')
                break
            else:
                full_conditions[self.__primary_keys[index]] = arg
        if conditions is not None:
            full_conditions.update(conditions)
        return full_conditions

    def check_primary_keys(self, dataset: pd.DataFrame or dict) -> bool:
        if len(self.__primary_keys) == 0:
            return True
        if isinstance(dataset, dict):
            return set(self.__primary_keys).issubset(set(list(dataset.keys())))
        if isinstance(dataset, pd.DataFrame):
            return set(self.__primary_keys).issubset(set(list(dataset.columns)))
        if isinstance(dataset, (list, tuple, set)):
            # Current do not check the content in list
            return True
        return False

    @staticmethod
    def judge_range_condition(var: any, cond: tuple) -> bool:
        if not isinstance(cond, tuple):
            print('Warning: %s is not a range condition.' % str(cond))
            return False
        if len(cond) > 1 and cond[0] is not None and var < cond[0]:
            return False
        if len(cond) > 2 and cond[1] is not None and var > cond[0]:
            return False
        return True




