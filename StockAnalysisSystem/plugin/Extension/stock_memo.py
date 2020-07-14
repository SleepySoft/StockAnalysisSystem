import errno
import os
import sys
import datetime
import traceback
import numpy as np
import pandas as pd
import pyqtgraph as pg

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QTimer, QDateTime, QPoint, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QButtonGroup, QDateTimeEdit, QApplication, QLabel, QTextEdit, QPushButton, QVBoxLayout, \
    QMessageBox, QWidget, QComboBox, QCheckBox, QRadioButton, QLineEdit, QAbstractItemView, QFileDialog
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent

from StockAnalysisSystem.core.config import *
from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.TagsLib import *
from StockAnalysisSystem.core.Utiltity.df_utility import *
from StockAnalysisSystem.core.Utiltity.ui_utility import *
from StockAnalysisSystem.core.Utiltity.TableViewEx import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem
from StockAnalysisSystem.core.Utiltity.securities_selector import SecuritiesSelector

root_path = os.path.dirname(os.path.abspath(__file__))
os.sys.path.append(root_path)

from StockMemo.MemoExtra import *
from StockMemo.MemoUtility import *
from StockMemo.StockChartUi import StockChartUi
from StockMemo.StockMemoEditor import StockMemoEditor


# ----------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------ Main UI -------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

NOTE = '''Stock Memo说明
1.Stock Memo相关的数据作为个人数据默认保存到系统用户目录下，更新程序不会破坏数据
2.如果用户自己指定保存目录，请手动复制已存在的文件到新目录下'''


# ------------------------------------------------ class StockMemoDeck -------------------------------------------------

class StockMemoDeck(QWidget):
    STATIC_HEADER = ['Security']

    def __init__(self, memo_data: StockMemoData):
        super(StockMemoDeck, self).__init__()
        self.__memo_data = memo_data

        self.__sas = self.__memo_data.get_sas()
        self.__memo_record: StockMemoRecord = self.__memo_data.get_memo_record()
        self.__memo_editor: StockMemoEditor = self.__memo_data.get_data('editor')
        self.__memo_editor.add_observer(self)
        self.__data_utility = self.__sas.get_data_hub_entry().get_data_utility() if self.__sas is not None else None

        self.__memo_extras = []
        self.__list_securities = self.__memo_record.get_all_security()

        # --------------- Widgets ---------------

        self.__memo_table = TableViewEx()
        self.__stock_selector = \
            SecuritiesSelector(self.__data_utility) if self.__data_utility is not None else QComboBox()
        self.__line_path = QLineEdit(self.__memo_data.get_root_path())
        self.__info_panel = QLabel(NOTE)
        self.__button_new = QPushButton('New')
        self.__button_filter = QPushButton('Filter')
        self.__button_browse = QPushButton('Browse')
        self.__button_black_list = QPushButton('Black List')

        self.init_ui()
        self.config_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        group_box, group_layout = create_v_group_box('Stock Memo')
        group_layout.addWidget(self.__memo_table)
        main_layout.addWidget(group_box, 10)

        group_box, group_layout = create_h_group_box('Edit')
        right_area = QVBoxLayout()
        group_layout.addWidget(self.__info_panel, 3)
        group_layout.addLayout(right_area, 7)

        line = horizon_layout([QLabel('股票选择：'), self.__stock_selector, self.__button_new, self.__button_filter],
                              [1, 10, 1, 1])
        right_area.addLayout(line)

        line = horizon_layout([QLabel('保存路径：'), self.__line_path, self.__button_browse],
                              [1, 10, 1])
        right_area.addLayout(line)

        line = horizon_layout([QLabel('其它功能：'), self.__button_black_list, QLabel('')],
                              [1, 1, 10])
        right_area.addLayout(line)

        main_layout.addWidget(group_box, 1)

    def config_ui(self):
        self.setMinimumSize(800, 600)
        self.__info_panel.setWordWrap(True)

        self.__memo_table.SetColumn(self.__memo_table_columns())
        self.__memo_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__memo_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.__memo_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.__memo_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.__memo_table.doubleClicked.connect(self.__on_memo_item_double_clicked)

        self.__button_browse.clicked.connect(self.__on_button_browse)
        self.__button_new.clicked.connect(self.__on_button_new_clicked)
        self.__button_filter.clicked.connect(self.__on_button_filter_clicked)

    def add_memo_extra(self, extra: MemoExtra):
        extra.set_memo_ui(self)
        self.__memo_extras.append(extra)

    def update_list(self):
        list_securities = [self.__list_securities] \
            if isinstance(self.__list_securities, str) else self.__list_securities
        self.__update_memo_securities_list(list_securities)

    # ------------------- Interface of StockMemoEditor.Observer ------------------

    def on_memo_updated(self):
        self.update_list()

    # ----------------------------------------------------------------------------

    def __on_button_browse(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Private Folder",
                                                      directory=self.__line_path.text()))
        if folder == '':
            return
        self.__line_path.setText(folder)

        # Save to system config
        self.__sas.get_config().set('memo_path', folder)
        self.__sas.get_config().save_config()

        # Update new path to memo extras
        self.__memo_data.set_root_path(folder)

        # TODO: Auto handle path update
        stock_tags: Tags = self.__memo_data.get_data('tags')
        if stock_tags is not None:
            stock_tags.load(os.path.join(folder, 'tags.json'))
        self.__memo_data.get_memo_record().load(os.path.join(folder, 'stock_memo.csv'))

    def __on_button_new_clicked(self):
        security = self.__stock_selector.get_input_securities()
        self.__memo_editor.select_security(security)
        self.__memo_editor.create_new_memo(now())
        self.__memo_editor.exec()

    def __on_button_filter_clicked(self):
        self.__list_securities = self.__stock_selector.get_input_securities()
        self.update_list()

    def __on_memo_item_double_clicked(self, index: QModelIndex):
        item_data = index.data(Qt.UserRole)
        if item_data is not None and isinstance(item_data, tuple):
            memo_extra, security = item_data
            memo_extra.security_entry(security)
            # print('Double Click on memo item: %s - %s' % (memo_extra.title_text(), security))

    def __update_memo_securities_list(self, securities: [str]):
        columns = self.__memo_table_columns()

        self.__memo_table.Clear()
        self.__memo_table.SetColumn(columns)
        self.__memo_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        for security in securities:
            self.__memo_table.AppendRow([''] * len(columns))
            row_count = self.__memo_table.RowCount()
            row = row_count - 1
            col = 0
            
            self.__memo_table.SetItemText(row, col, security)
            self.__memo_table.SetItemData(row, col, security)

            for memo_extra in self.__memo_extras:
                col += 1
                text = memo_extra.security_entry_text(security)
            
                self.__memo_table.SetItemText(row, col, text)
                self.__memo_table.SetItemData(row, col, (memo_extra, security))
                
                # _item = self.__memo_table.GetItem(row, col)
                # _item.clicked.connect(partial(self.__on_memo_item_clicked, _item, security, memo_extra))

    def __memo_table_columns(self) -> [str]:
        return StockMemoDeck.STATIC_HEADER + [memo_extra.title_text() for memo_extra in self.__memo_extras]


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': 'b3767a36-123f-45ab-bfad-f352c2b48354',
        'plugin_name': 'History',
        'plugin_version': '0.0.0.1',
        'tags': ['History', 'Sleepy'],
    }


def plugin_adapt(method: str) -> bool:
    return method in ['widget']


def plugin_capacities() -> list:
    return [
        'widget',
    ]


# ----------------------------------------------------------------------------------------------------------------------

sasEntry = None
memoData: StockMemoData = None


def init(sas: StockAnalysisSystem) -> bool:
    try:
        global sasEntry
        sasEntry = sas
        global memoData
        memoData = StockMemoData(sasEntry)
    except Exception as e:
        print(e)
        return False
    finally:
        pass
    return True


def widget(parent: QWidget) -> (QWidget, dict):
    global memoData
    memoData.set_data('tags', Tags(os.path.join(memoData.get_root_path(), 'tags.json')))
    memoData.set_data('editor', StockMemoEditor(memoData))

    memo_ui = StockMemoDeck(memoData)
    memo_ui.add_memo_extra(MemoExtra_MemoContent(memoData))
    memo_ui.add_memo_extra(MemoExtra_MemoHistory(memoData))
    memo_ui.add_memo_extra(MemoExtra_StockTags(memoData))
    memo_ui.update_list()

    return memo_ui, {'name': '股票笔记', 'show': False}


# ------------------------------------------------ File Entry : main() -------------------------------------------------

def main():
    app = QApplication(sys.argv)
    # dlg = WrapperQDialog(StockMemoEditor(None, None))
    
    stock_memo = StockMemoDeck(None)
    stock_memo.add_memo_extra(DummyMemoExtra('Column1'))
    stock_memo.add_memo_extra(DummyMemoExtra('Column2'))
    stock_memo.add_memo_extra(DummyMemoExtra('Column3'))
    stock_memo.add_memo_extra(DummyMemoExtra('Column4'))
    stock_memo.add_memo_extra(DummyMemoExtra('Column5'))
    stock_memo.update_list()
    dlg = WrapperQDialog(stock_memo)
    
    dlg.exec()
    exit(app.exec_())


# ----------------------------------------------------------------------------------------------------------------------

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




















