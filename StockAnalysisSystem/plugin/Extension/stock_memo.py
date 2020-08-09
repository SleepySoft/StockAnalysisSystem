import errno
import os
import sys
import datetime
import traceback
import numpy as np
import pandas as pd

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QTimer, QDateTime, QPoint, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QButtonGroup, QDateTimeEdit, QApplication, QLabel, QTextEdit, QPushButton, QVBoxLayout, \
    QMessageBox, QWidget, QComboBox, QCheckBox, QRadioButton, QLineEdit, QAbstractItemView, QFileDialog, QSpinBox
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

try:
    from .StockMemo.MemoExtra import *
    from .StockMemo.MemoUtility import *
    from .StockMemo.StockChartUi import StockChartUi
    from .StockMemo.StockMemoEditor import StockMemoEditor
except Exception as e:
    root_path = os.path.dirname(os.path.abspath(__file__))
    os.sys.path.append(root_path)

    from StockMemo.MemoExtra import *
    from StockMemo.MemoUtility import *
    from StockMemo.StockChartUi import StockChartUi
    from StockMemo.StockMemoEditor import StockMemoEditor
finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------ Main UI -------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

NOTE = '''说明
1.笔记相关的数据作为个人数据默认保存到系统用户目录下
2.用户可以选择笔记保存路径，请注意备份自己的数据
3.列表默认列出有笔记的股票，可以通过“股票选择”筛选并列出其它股票'''


# ------------------------------------------------ class StockMemoDeck -------------------------------------------------

class StockMemoDeck(QWidget):
    STATIC_HEADER = ['Code', 'Name']

    def __init__(self, memo_data: StockMemoData):
        super(StockMemoDeck, self).__init__()
        self.__memo_data = memo_data

        if self.__memo_data is not None:
            self.__memo_data.add_observer(self)

            self.__sas = self.__memo_data.get_sas()
            self.__memo_record: StockMemoRecord = self.__memo_data.get_memo_record()
            self.__memo_editor: StockMemoEditor = self.__memo_data.get_data('editor')
            self.__data_utility = self.__sas.get_data_hub_entry().get_data_utility() if self.__sas is not None else None
        else:
            # For layout debug
            self.__sas = None
            self.__memo_record = None
            self.__memo_editor = None
            self.__data_utility = None

        self.__memo_extras = []
        self.__list_securities = []
        self.__show_securities = []

        # ---------------- Page -----------------

        self.__page = 1
        self.__item_per_page = 20

        self.__button_first = QPushButton('|<')
        self.__button_prev = QPushButton('<')
        self.__spin_page = QSpinBox()
        self.__label_total_page = QLabel('/ 1')
        self.__button_jump = QPushButton('GO')
        self.__button_next = QPushButton('>')
        self.__button_last = QPushButton('>|')

        self.__button_reload = QPushButton('Reload')
        self.__check_show_black_list = QCheckBox('Black List')

        # --------------- Widgets ---------------

        self.__memo_table = TableViewEx()
        self.__stock_selector = \
            SecuritiesSelector(self.__data_utility) if self.__data_utility is not None else QComboBox()
        self.__line_path = QLineEdit(self.__memo_data.get_root_path() if self.__memo_data is not None else root_path)
        self.__info_panel = QLabel(NOTE)
        self.__button_new = QPushButton('New')
        self.__button_filter = QPushButton('Filter')
        self.__button_browse = QPushButton('Browse')
        # self.__button_black_list = QPushButton('Black List')

        self.__layout_extra = QHBoxLayout()

        self.init_ui()
        self.config_ui()

        self.show_securities(self.__memo_record.get_all_security() if self.__memo_record is not None else [])

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Page control
        page_control_line = QHBoxLayout()
        page_control_line.addWidget(self.__button_reload, 1)
        page_control_line.addWidget(self.__check_show_black_list, 1)

        page_control_line.addWidget(QLabel(''), 99)
        page_control_line.addWidget(self.__button_first, 1)
        page_control_line.addWidget(self.__button_prev, 1)
        page_control_line.addWidget(self.__spin_page, 1)
        page_control_line.addWidget(self.__label_total_page, 1)
        page_control_line.addWidget(self.__button_jump, 1)
        page_control_line.addWidget(self.__button_next, 1)
        page_control_line.addWidget(self.__button_last, 1)

        group_box, group_layout = create_v_group_box('Stock Memo')
        group_layout.addWidget(self.__memo_table)
        group_layout.addLayout(page_control_line)
        main_layout.addWidget(group_box, 10)

        group_box, group_layout = create_h_group_box('Edit')
        right_area = QVBoxLayout()
        group_layout.addWidget(self.__info_panel, 4)
        group_layout.addLayout(right_area, 6)

        line = horizon_layout([QLabel('股票选择：'), self.__stock_selector, self.__button_filter, self.__button_new],
                              [1, 10, 1, 1])
        right_area.addLayout(line)

        line = horizon_layout([QLabel('保存路径：'), self.__line_path, self.__button_browse],
                              [1, 10, 1])
        right_area.addLayout(line)

        # line = horizon_layout([QLabel('其它功能：'), self.__button_black_list, QLabel('')],
        #                       [1, 1, 10])

        self.__layout_extra.addWidget(QLabel('其它功能：'))
        self.__layout_extra.addStretch()
        right_area.addLayout(self.__layout_extra)

        main_layout.addWidget(group_box, 1)

    def config_ui(self):
        self.setMinimumSize(800, 600)
        self.__info_panel.setWordWrap(True)

        # -------------- Page Control --------------

        self.__button_first.clicked.connect(partial(self.__on_page_control, '|<'))
        self.__button_prev.clicked.connect(partial(self.__on_page_control, '<'))
        self.__button_jump.clicked.connect(partial(self.__on_page_control, 'g'))
        self.__button_next.clicked.connect(partial(self.__on_page_control, '>'))
        self.__button_last.clicked.connect(partial(self.__on_page_control, '>|'))

        self.__button_reload.clicked.connect(self.__on_button_reload)

        self.__check_show_black_list.setChecked(False)
        self.__check_show_black_list.clicked.connect(self.__on_check_show_black_list)

        self.__memo_table.SetColumn(self.__memo_table_columns())
        self.__memo_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__memo_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.__memo_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.__memo_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.__memo_table.doubleClicked.connect(self.__on_memo_item_double_clicked)

        self.__button_new.clicked.connect(self.__on_button_new_clicked)
        self.__button_browse.clicked.connect(self.__on_button_browse)
        self.__button_filter.clicked.connect(self.__on_button_filter_clicked)

        self.__button_filter.setDefault(True)
        line_editor = self.__stock_selector.lineEdit()
        if line_editor is not None:
            line_editor.returnPressed.connect(self.__on_button_filter_clicked)

    def add_memo_extra(self, extra: MemoExtra):
        extra.set_memo_ui(self)
        self.__memo_extras.append(extra)

        global_entry_text = extra.global_entry_text()
        if str_available(global_entry_text):
            button = QPushButton(global_entry_text)
            button.clicked.connect(partial(self.__on_button_global_entry, extra))
            self.__layout_extra.insertWidget(1, button)

    def update_list(self):
        self.__update_memo_securities_list()

    def show_securities(self, securities: [str]):
        self.__update_securities(securities)
        self.__update_memo_securities_list()

    # ------------------- Interface of StockMemoData.Observer --------------------

    # def on_memo_updated(self):
    #     self.update_list()

    def on_data_updated(self, name: str, data: any):
        nop(data)
        if name in ['memo_record', 'tags']:
            self.update_list()

    # ----------------------------------------------------------------------------

    def __on_page_control(self, button_mark: str):
        new_page = self.__page
        if button_mark == '|<':
            new_page = 0
        elif button_mark == '<':
            new_page -= 1
        elif button_mark == 'g':
            new_page = self.__spin_page.value()
        elif button_mark == '>':
            new_page += 1
        elif button_mark == '>|':
            new_page = self.__max_page()

        new_page = max(1, new_page)
        new_page = min(self.__max_page(), new_page)

        if self.__page != new_page:
            self.__page = new_page
            self.__spin_page.setValue(self.__page)
            self.update_list()

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
        input_security = self.__stock_selector.get_input_securities()
        list_securities = self.__data_utility.guess_securities(input_security)
        self.show_securities(list_securities)

    def __on_button_reload(self):
        self.show_securities(self.__memo_record.get_all_security() if self.__memo_record is not None else [])

    def __on_check_show_black_list(self):
        self.__update_securities()
        self.__update_memo_securities_list()

    def __on_memo_item_double_clicked(self, index: QModelIndex):
        item_data = index.data(Qt.UserRole)
        if item_data is not None and isinstance(item_data, tuple):
            memo_extra, security = item_data
            memo_extra.security_entry(security)
            # print('Double Click on memo item: %s - %s' % (memo_extra.title_text(), security))

    def __on_button_global_entry(self, extra: MemoExtra):
        extra.global_entry()

    def __update_memo_securities_list(self, securities: [str] or None = None):
        if securities is None:
            securities = self.__show_securities

        columns = self.__memo_table_columns()

        self.__memo_table.Clear()
        self.__memo_table.SetColumn(columns)

        index = []
        offset = (self.__page - 1) * self.__item_per_page

        for i in range(offset, offset + self.__item_per_page):
            if i < 0 or i >= len(securities):
                continue
            security = securities[i]
            index.append(str(i + 1))

            self.__memo_table.AppendRow([''] * len(columns))
            row_count = self.__memo_table.RowCount()
            row = row_count - 1
            
            col = 0
            self.__memo_table.SetItemText(row, col, security)
            self.__memo_table.SetItemData(row, col, security)

            col = 1
            self.__memo_table.SetItemText(row, col, self.__data_utility.stock_identity_to_name(security))

            for memo_extra in self.__memo_extras:
                if not str_available(memo_extra.title_text()):
                    continue

                col += 1
                text = memo_extra.security_entry_text(security)
            
                self.__memo_table.SetItemText(row, col, text)
                self.__memo_table.SetItemData(row, col, (memo_extra, security))
                
                # _item = self.__memo_table.GetItem(row, col)
                # _item.clicked.connect(partial(self.__on_memo_item_clicked, _item, security, memo_extra))

        model = self.__memo_table.model()
        model.setVerticalHeaderLabels(index)

    def __update_securities(self, list_securities: [str] or None = None):
        if list_securities is None:
            # Just refresh the show securities
            pass
        else:
            self.__list_securities = list_securities \
                if isinstance(list_securities, (list, tuple)) else [list_securities]
        self.__update_show_securities()
        self.__update_page_control()

    def __update_show_securities(self):
        self.__show_securities = self.__list_securities

        show_black_list = self.__check_show_black_list.isChecked()
        if not show_black_list:
            black_list: BlackList = self.__memo_data.get_data('black_list')
            if black_list is not None:
                black_list_securities = black_list.all_black_list()
                self.__show_securities = list(set(self.__show_securities).difference(set(black_list_securities)))

    def __memo_table_columns(self) -> [str]:
        return StockMemoDeck.STATIC_HEADER + [memo_extra.title_text()
                                              for memo_extra in self.__memo_extras
                                              if str_available(memo_extra.title_text())]

    def __max_page(self) -> int:
        return (len(self.__show_securities) + self.__item_per_page - 1) // self.__item_per_page

    def __update_page_control(self):
        self.__page = 1
        max_page = self.__max_page()
        self.__spin_page.setValue(1)
        self.__spin_page.setMinimum(1)
        self.__spin_page.setMaximum(max_page)
        self.__label_total_page.setText('/ %s' % max_page)


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


def __build_memo_data() -> StockMemoData:
    global memoData
    memoData.set_data('tags', Tags(os.path.join(memoData.get_root_path(), 'tags.json')))
    memoData.set_data('editor', StockMemoEditor(memoData))
    memoData.set_data('black_list', BlackList(memoData))
    return memoData


def __build_memo_extra(memo_data: StockMemoData) -> [MemoExtra]:
    return [
        MemoExtra_MemoContent(memo_data),
        MemoExtra_MemoHistory(memo_data),
        MemoExtra_StockTags(memo_data),
        MemoExtra_Analysis(memo_data),
        MemoExtra_BlackList(memo_data),
    ]


def __register_sys_call():
    if sasEntry is None:
        return
    black_list: BlackList = memoData.get_data('black_list')
    if black_list is not None:
        sasEntry.register_sys_call('get_black_list_data', {}, '', black_list.get_black_list_data)


def __register_extra_data():
    if sasEntry is None:
        return
    sasEntry.get_data_hub_entry().reg_data_extra('black_list', memoData.get_data('black_list'))


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
    memo_data = __build_memo_data()
    memo_extra = __build_memo_extra(memo_data)

    memo_ui = StockMemoDeck(memoData)
    for extra in memo_extra:
        memo_ui.add_memo_extra(extra)
    memo_ui.update_list()

    __register_sys_call()
    __register_extra_data()

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




















