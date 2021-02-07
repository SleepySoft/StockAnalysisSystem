from StockAnalysisSystem.core.Utility.TagsLib import *
from StockAnalysisSystem.core.Utility.WaitingWindow import *
from StockAnalysisSystem.core.Utility.AnalyzerUtility import *

try:
    from .StockMemo import StockMemo
except Exception as e:
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.append(root_path)

    from StockMemo.StockMemo import StockMemo
finally:
    pass


# -------------------------------------------------- class BlackList ---------------------------------------------------

class BlackList:
    BLACK_LIST_TAGS = '黑名单'
    RECORD_CLASSIFY = 'black_list'

    def __init__(self, stock_memo: StockMemo, stock_tags: Tags):
        self.__stock_tag: Tags = stock_tags
        self.__stock_memo: StockMemo = stock_memo

        self.__data_loaded = False
        self.__black_list_securities: list = []
        self.__black_list_record: pd.DataFrame = None

        # TODO: It may spends lot of time
        self.__collect_black_list_data()

    # ----------------------------------------------------

    def save_black_list(self):
        if self.__data_valid() and self.__data_loaded:
            self.__stock_tag.save()
            self.__stock_memo.stock_memo_save()
            # self.__memo_data.broadcast_data_updated('tags')
            # self.__memo_data.broadcast_data_updated('memo_record')
        else:
            print('Warning: Black list has not been Loaded yet.')

    def in_black_list(self, security: str):
        return security in self.__black_list_securities

    def all_black_list(self) -> []:
        return self.__black_list_securities

    def add_to_black_list(self, security: str, reason: str):
        if not self.__data_valid() or not self.__data_loaded:
            print('Warning: Black list has not been Loaded yet.')
            return
        if security in self.__black_list_securities:
            return
        self.__memo_record.add_record({
            'time': now(),
            'security': security,
            'brief': '加入黑名单',
            'content': reason,
            'classify': BlackList.RECORD_CLASSIFY,
        }, False)
        self.__stock_tag.add_obj_tags(security, BlackList.BLACK_LIST_TAGS)
        self.__black_list_securities.append(security)

    def remove_from_black_list(self, security: str, reason: str):
        if not self.__data_valid() or not self.__data_loaded:
            print('Warning: Black list has not been Loaded yet.')
            return
        if security not in self.__black_list_securities:
            return
        self.__memo_record.add_record({
            'time': now(),
            'security': security,
            'brief': '移除黑名单',
            'content': reason,
            'classify': BlackList.RECORD_CLASSIFY,
        }, False)
        self.__stock_tag.remove_obj_tags(security, BlackList.BLACK_LIST_TAGS)
        self.__black_list_securities.remove(security)

    def get_black_list_data(self) -> pd.DataFrame:
        return self.__black_list_record

    def reload_black_list_data(self):
        self.__collect_black_list_data()

    # ---------------------------------------------------------------------------------

    def __data_valid(self) -> bool:
        return self.__stock_tag is not None and self.__stock_memo is not None

    def __collect_black_list_data(self):
        if self.__data_valid:
            black_list_securities = self.__stock_tag.objs_from_tags('黑名单') if self.__stock_tag is not None else []
            df = self.__stock_memo.raw_record().get_records({'classify': BlackList.RECORD_CLASSIFY})
            if df is not None and not df.empty:
                df = df.sort_values('time')
                df = df.groupby('security', as_index=False, sort=False).last()
                df = df[df['security'].isin(black_list_securities)]
            self.__black_list_securities = black_list_securities
            self.__black_list_record = df
            self.__data_loaded = True




