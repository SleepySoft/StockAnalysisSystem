import os

from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.TagsLib import *
from StockAnalysisSystem.core.Utiltity.df_utility import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.WaitingWindow import *
from StockAnalysisSystem.core.Utiltity.AnalyzerUtility import *

try:
    # Only for pycharm indicating imports
    from .BlackList import *
    from .MemoUtility import *
    from .StockChartUi import StockChartUi
    from .StockMemoEditor import StockMemoEditor
except Exception as e:
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.append(root_path)

    from StockMemo.BlackList import *
    from StockMemo.MemoUtility import *
    from StockMemo.StockChartUi import StockChartUi
    from StockMemo.StockMemoEditor import StockMemoEditor
finally:
    pass
pass

# ------------------------------------------------ Memo Extra Interface ------------------------------------------------

class MemoExtra:
    def __init__(self):
        self.__memo_ui = None

    def set_memo_ui(self, memo_ui):
        self.__memo_ui = memo_ui

    # def notify_memo_ui_update(self):
    #     self.__memo_ui.update_list()

    def global_entry(self):
        pass

    def security_entry(self, security: str):
        pass

    def title_text(self) -> str:
        pass

    def global_entry_text(self) -> str:
        pass

    def security_entry_text(self, security: str) -> str:
        pass


class DummyMemoExtra(MemoExtra):
    def __init__(self, title_text: str):
        self.__title_text = title_text
        super(DummyMemoExtra, self).__init__()

    def global_entry(self):
        print('global_entry')

    def security_entry(self, security: str):
        print('security_entry')

    def title_text(self) -> str:
        return self.__title_text

    def global_entry_text(self) -> str:
        return 'DummyMemoExtra'

    def security_entry_text(self, security: str) -> str:
        return self.__title_text + ': ' + security


# ---------------------------------------------------- Memo Extras -----------------------------------------------------

# --------------------------------- Editor ---------------------------------

class MemoExtra_MemoContent(MemoExtra):
    def __init__(self, memo_data: StockMemoData):
        self.__memo_data = memo_data
        self.__memo_editor: StockMemoEditor = self.__memo_data.get_data('editor') \
            if self.__memo_data is not None else None
        self.__memo_record: StockMemoRecord = self.__memo_data.get_memo_record() \
            if self.__memo_data is not None else None
        super(MemoExtra_MemoContent, self).__init__()

    def global_entry(self):
        pass

    def security_entry(self, security: str):
        if self.__memo_editor is not None:
            self.__memo_editor.select_security(security)
            self.__memo_editor.select_memo_by_list_index(0)
            self.__memo_editor.exec()

    def title_text(self) -> str:
        return 'Memo'

    def global_entry_text(self) -> str:
        return ''

    def security_entry_text(self, security: str) -> str:
        if self.__memo_record is None:
            return '-'
        df = self.__memo_record.get_records({'security': security})
        if df is not None and not df.empty:
            df.sort_values('time')
            brief = df.iloc[-1]['brief']
            content = df.iloc[-1]['content']
            text = brief if str_available(brief) else content
            # https://stackoverflow.com/a/2873416/12929244
            return text[:30] + (text[30:] and '...')
        return ''


# --------------------------------- History ---------------------------------

class MemoExtra_MemoHistory(MemoExtra):
    def __init__(self, memo_data: StockMemoData):
        self.__memo_data = memo_data
        self.__memo_history = StockChartUi(self.__memo_data)
        super(MemoExtra_MemoHistory, self).__init__()

    def global_entry(self):
        pass

    def security_entry(self, security: str):
        self.__memo_history.show_security(security, True)
        self.__memo_history.setVisible(True)

    def title_text(self) -> str:
        return 'Chart'

    def global_entry_text(self) -> str:
        return ''

    def security_entry_text(self, security: str) -> str:
        return 'View'


# ---------------------------------- Tags ----------------------------------

class MemoExtra_StockTags(MemoExtra):
    PRESET_TAGS = ['黑名单', '灰名单', '关注']

    def __init__(self, memo_data: StockMemoData):
        self.__memo_data = memo_data
        super(MemoExtra_StockTags, self).__init__()
        self.__stock_tags: Tags = self.__memo_data.get_data('tags')
        self.__stock_tags_ui: TagsUi = TagsUi(self.__stock_tags)
        self.__stock_tags_ui.on_ensure(self.__on_tags_ui_ensure)
        self.__current_stock = ''
        self.__stock_tags.set_obj_tags('', MemoExtra_StockTags.PRESET_TAGS)

    def __on_tags_ui_ensure(self):
        tags = self.__stock_tags_ui.get_selected_tags()
        self.__stock_tags_ui.close()
        self.__stock_tags.set_obj_tags(self.__current_stock, tags)
        self.__stock_tags.save()
        self.__memo_data.broadcast_data_updated('tags')

    def global_entry(self):
        pass

    def security_entry(self, security: str):
        tags = self.__stock_tags.tags_of_objs(security)
        self.__stock_tags_ui.reload_tags()
        self.__stock_tags_ui.select_tags(tags)
        self.__stock_tags_ui.setVisible(True)
        self.__current_stock = security

    def title_text(self) -> str:
        return 'Tags'

    def global_entry_text(self) -> str:
        return ''

    def security_entry_text(self, security: str) -> str:
        tags = self.__stock_tags.tags_of_objs(security)
        return Tags.tags_to_str(tags)


# -------------------------------- Analysis --------------------------------

class MemoExtra_Analysis(MemoExtra):
    def __init__(self, memo_data: StockMemoData):
        self.__memo_data = memo_data
        super(MemoExtra_Analysis, self).__init__()

    def global_entry(self):
        pass

    def security_entry(self, security: str):
        strategy_entry = self.__memo_data.get_sas().get_strategy_entry()

        selector = AnalyzerSelector(strategy_entry)
        selector.exec()
        if not selector.is_ok():
            return

        analyzers = selector.get_select_strategy()
        if len(analyzers) == 0:
            return

        with futures.ThreadPoolExecutor(max_workers=1) as executor:
            future: futures.Future = executor.submit(self.__analysis, security, analyzers)
            if not WaitingWindow.wait_future('分析计算中...', future, None):
                return
            df = future.result(0)

        if df is None:
            return

        # analyzer_info = strategy_entry.analyzer_info()
        # analyzers = [uuid for uuid, _, _, _ in analyzer_info]
        #
        # result = strategy_entry.analysis_advance(security, analyzers, (years_ago(5), now()))
        #
        # df = analysis_result_list_to_single_stock_report(result, security)
        # df = df.fillna('-')
        # df = df.rename(columns=strategy_entry.strategy_name_dict())

        table = QTableWidget()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.setMinimumSize(800, 600)
        write_df_to_qtable(df, table, True)

        dlg = WrapperQDialog(table)
        dlg.setWindowTitle('Analysis Result')
        dlg.exec()

    def title_text(self) -> str:
        return 'Analysis'

    def global_entry_text(self) -> str:
        return ''

    def security_entry_text(self, security: str) -> str:
        return 'Go'

    def __analysis(self, security: str, analyzers: [str]) -> pd.DataFrame:
        strategy_entry = self.__memo_data.get_sas().get_strategy_entry()
        result = strategy_entry.analysis_advance(security, analyzers, (years_ago(5), now()))
        df = analysis_result_list_to_single_stock_report(result, security)
        df = df.fillna('-')
        df = df.rename(columns=strategy_entry.strategy_name_dict())
        return df


# -------------------------------- Analysis --------------------------------

class MemoExtra_BlackList(MemoExtra):
    def __init__(self, memo_data: StockMemoData):
        self.__memo_data = memo_data
        super(MemoExtra_BlackList, self).__init__()

    def global_entry(self):
        sas = self.__memo_data.get_sas()
        black_list = self.__memo_data.get_data('black_list')
        black_list_ui = BlackListUi(black_list, sas)
        dlg = WrapperQDialog(black_list_ui)
        dlg.exec()

    def security_entry(self, security: str):
        pass

    def title_text(self) -> str:
        return ''

    def global_entry_text(self) -> str:
        return 'Black List'

    def security_entry_text(self, security: str) -> str:
        return ''

















