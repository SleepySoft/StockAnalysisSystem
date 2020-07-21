import os
import errno

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QTimer, QDateTime, QPoint, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QButtonGroup, QDateTimeEdit, QApplication, QLabel, QTextEdit, QPushButton, QVBoxLayout, \
    QMessageBox, QWidget, QComboBox, QCheckBox, QRadioButton, QLineEdit, QAbstractItemView, QFileDialog, QDialog
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent

from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.TagsLib import *
from StockAnalysisSystem.core.Utiltity.CsvRecord import *
from StockAnalysisSystem.core.Utiltity.ui_utility import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.securities_selector import SecuritiesSelector

try:
    from .MemoUtility import *
except Exception as e:
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.append(root_path)

    from StockMemo.MemoUtility import *
finally:
    pass


# ----------------------------------------------- class StockMemoRecord ------------------------------------------------

class BlackList:
    RECORD_CLASSIFY = 'black_list'

    def __init__(self, memo_data: StockMemoData):
        self.__memo_data = memo_data
        self.__stock_tag: Tags = memo_data.get_data('tags') if memo_data is not None else None
        self.__memo_record: CsvRecord = memo_data.get_memo_record() if memo_data is not None else None

        self.__data_loaded = False
        self.__black_list_securities: list = []
        self.__black_list_record: pd.DataFrame = None

    # ----------------------------------------------------

    def save_black_list(self):
        if self.__data_valid() and self.__data_loaded:
            self.__stock_tag.save()
            self.__memo_record.save()
            self.__memo_data.broadcast_data_updated('tags')
            self.__memo_data.broadcast_data_updated('memo_record')

    def add_to_black_list(self, security: str, reason: str):
        if self.__data_valid() and self.__data_loaded:
            return
        if security in self.__black_list_securities:
            return
        self.__memo_record.add_record({
            'time': now(),
            'security': security,
            'brief': BlackList.RECORD_CLASSIFY,
            'content': reason,
            'classify': 'memo',
        }, False)
        self.__stock_tag.set_obj_tags()

    def remove_from_black_list(self, security: str, reason: str):
        pass

    def reload_black_list_data(self):
        self.__collect_black_list_data()

    # ---------------------------------------------------------------------------------

    def __data_valid(self) -> bool:
        return self.__memo_data is not None and self.__stock_tag is not None and self.__memo_record is not None

    def __collect_black_list_data(self):
        if self.__data_valid:
            black_list_securities = self.__stock_tag.objs_from_tags('黑名单') if self.__stock_tag is not None else []
            df = self.__memo_record.get_records({'classify': BlackList.RECORD_CLASSIFY})
            if df is not None and not df.empty:
                df = df.sort_values('time')
                df = df.groupby('security').last()
                df = df[df['security'] in black_list_securities]
            self.__black_list_securities = black_list_securities
            self.__black_list_record = df
            self.__data_loaded = True


















