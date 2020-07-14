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
from StockAnalysisSystem.porting.vnpy_chart import *
from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.TagsLib import *
from StockAnalysisSystem.core.Utiltity.CsvRecord import *
from StockAnalysisSystem.core.Utiltity.df_utility import *
from StockAnalysisSystem.core.Utiltity.ui_utility import *
from StockAnalysisSystem.core.Utiltity.TableViewEx import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem
from StockAnalysisSystem.core.Utiltity.securities_selector import SecuritiesSelector


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
    memo_path = os.path.join(project_path, 'Data', 'StockMemo')
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


# ----------------------------------------------- class StockMemoEditor ------------------------------------------------

class StockMemoEditor(QDialog):
    LIST_HEADER = ['Time', 'Preview']

    class Observer:
        def __init__(self):
            pass

        def on_memo_updated(self):
            pass

    def __init__(self, memo_data: StockMemoData, parent: QWidget = None):
        self.__memo_data = memo_data
        super(StockMemoEditor, self).__init__(parent)

        # The filter of left list
        # self.__filter_identity: str = ''
        # self.__filter_datetime: datetime.datetime = None

        # The stock that selected by combobox or outer setting
        self.__current_stock = None

        # The current index of editing memo
        # Not None: Update exists
        # None: Create new
        self.__current_index = None

        # The memo list that displaying in the left list
        self.__current_memos: pd.DataFrame = None

        self.__observers = []

        self.__sas = self.__memo_data.get_sas() if self.__memo_data is not None else None
        self.__memo_record = self.__memo_data.get_memo_record() if self.__memo_data is not None else None

        data_utility = self.__sas.get_data_hub_entry().get_data_utility() if self.__sas is not None else None
        self.__combo_stock = SecuritiesSelector(data_utility)
        self.__table_memo_index = EasyQTableWidget()

        self.__datetime_time = QDateTimeEdit(QDateTime().currentDateTime())
        self.__line_brief = QLineEdit()
        self.__text_record = QTextEdit()

        self.__button_new = QPushButton('New')
        self.__button_apply = QPushButton('Save')

        self.init_ui()
        self.config_ui()

    def init_ui(self):
        root_layout = QHBoxLayout()
        self.setLayout(root_layout)

        group_box, group_layout = create_v_group_box('')
        group_layout.addWidget(self.__combo_stock, 1)
        group_layout.addWidget(self.__table_memo_index, 99)
        root_layout.addWidget(group_box, 4)

        group_box, group_layout = create_v_group_box('')
        group_layout.addLayout(horizon_layout([QLabel('Time：'), self.__datetime_time, self.__button_new], [1, 99, 1]))
        group_layout.addLayout(horizon_layout([QLabel('Brief：'), self.__line_brief], [1, 99]))
        group_layout.addLayout(horizon_layout([QLabel('Content：'), QLabel('')], [1, 99]))
        group_layout.addWidget(self.__text_record)
        group_layout.addLayout(horizon_layout([QLabel(''), self.__button_apply], [99, 1]))
        root_layout.addWidget(group_box, 6)

        self.setMinimumSize(500, 600)

    def config_ui(self):
        self.setWindowTitle('Memo Editor')
        self.__datetime_time.setCalendarPopup(True)

        self.__combo_stock.setEditable(False)
        self.__combo_stock.currentIndexChanged.connect(self.on_combo_select_changed)

        self.__table_memo_index.insertColumn(0)
        self.__table_memo_index.insertColumn(0)
        self.__table_memo_index.setHorizontalHeaderLabels(StockMemoEditor.LIST_HEADER)
        self.__table_memo_index.setSelectionMode(QAbstractItemView.SingleSelection)
        self.__table_memo_index.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__table_memo_index.itemSelectionChanged.connect(self.on_table_selection_changed)
        self.__table_memo_index.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.__button_new.clicked.connect(self.on_button_new)
        self.__button_apply.clicked.connect(self.on_button_apply)

        # self.setWindowFlags(
        #     QtCore.Qt.Window |
        #     QtCore.Qt.CustomizeWindowHint |
        #     QtCore.Qt.WindowTitleHint |
        #     QtCore.Qt.WindowCloseButtonHint |
        #     QtCore.Qt.WindowStaysOnTopHint
        # )

    def on_button_new(self):
        if not str_available(self.__current_stock):
            QMessageBox.information(self, '错误', '请选择需要做笔记的股票', QMessageBox.Ok, QMessageBox.Ok)
        self.create_new_memo(None)
        self.__trigger_memo_updated()
        
    # ['time', 'security', 'brief', 'content', 'classify']

    def on_button_apply(self):
        _time = self.__datetime_time.dateTime().toPyDateTime()
        brief = self.__line_brief.text()
        content = self.__text_record.toPlainText()

        if not str_available(brief):
            QMessageBox.information(self, '错误', '请至少填写笔记摘要', QMessageBox.Ok, QMessageBox.Ok)
            return

        if self.__current_index is not None:
            ret = self.__memo_record.update_record(self.__current_index, {
                'time': _time,
                'brief': brief,
                'content': content,
                'classify': 'memo',
            }, True)
        else:
            if str_available(self.__current_stock):
                ret, index = self.__memo_record.add_record({
                    'time': _time,
                    'security': self.__current_stock,
                    'brief': brief,
                    'content': content,
                    'classify': 'memo',
                }, True)
                self.__current_index = index
            else:
                ret = False
                QMessageBox.information(self, '错误', '没有选择做笔记的股票', QMessageBox.Ok, QMessageBox.Ok)
        if ret:
            self.load_security_memo(self.__current_stock)

            if self.__current_index is not None:
                self.select_memo_by_memo_index(self.__current_index)
            else:
                self.select_memo_by_list_index(0)
        self.__trigger_memo_updated()

    def on_combo_select_changed(self):
        input_securities = self.__combo_stock.get_input_securities()
        if input_securities != self.__current_stock:
            self.load_security_memo(input_securities)

    def on_table_selection_changed(self):
        sel_index = self.__table_memo_index.GetCurrentIndex()
        if sel_index < 0:
            return
        sel_item = self.__table_memo_index.item(sel_index, 0)
        if item is None:
            return
        df_index = sel_item.data(Qt.UserRole)
        self.load_edit_memo(df_index)

    # --------------------------------------------------------------------------------------------

    def add_observer(self, ob: Observer):
        self.__observers.append(ob)
        
    def __trigger_memo_updated(self):
        for ob in self.__observers:
            ob.on_memo_updated()

    # ------------------------------------- Select Functions -------------------------------------
    #                     Will update UI control, which will trigger the linkage

    def select_security(self, security: str):
        self.__combo_stock.select_security(security, True)

    def select_memo_by_day(self, _time: datetime.datetime):
        if self.__current_memos is None or self.__current_memos.empty:
            self.create_new_memo(_time)
            return

        df = self.__current_memos
        time_serial = df['time'].dt.normalize()
        select_df = df[time_serial == _time.replace(hour=0, minute=0, second=0, microsecond=0)]

        select_index = None
        for index, row in select_df.iterrows():
            select_index = index
            break

        if select_index is not None:
            self.select_memo_by_memo_index(select_index)
        else:
            self.create_new_memo(_time)

    def select_memo_by_memo_index(self, memo_index: int):
        for row in range(0, self.__table_memo_index.rowCount()):
            row_memo_index = self.__table_memo_index.item(row, 0).data(Qt.UserRole)
            if row_memo_index == memo_index:
                self.__table_memo_index.selectRow(row)
                break

    def select_memo_by_list_index(self, list_index: int):
        if list_index >= 0:
            self.__table_memo_index.selectRow(list_index)
            self.__table_memo_index.scrollToItem(self.__table_memo_index.item(list_index, 0))
        else:
            self.__table_memo_index.clearSelection()
            self.create_new_memo(now())

    # ----------------------------------- Select and Load Logic -----------------------------------

    def load_security_memo(self, security: str):
        condition = {'classify': 'memo'}
        if str_available(security):
            condition['security'] = security
        df = self.__memo_record.get_records(condition)

        self.__current_memos = df
        self.__current_stock = security

        self.update_memo_list()

    def update_memo_list(self):
        self.__table_memo_index.clear()
        self.__table_memo_index.setRowCount(0)
        self.__table_memo_index.setHorizontalHeaderLabels(StockMemoEditor.LIST_HEADER)

        for index, row in self.__current_memos.iterrows():
            row_index = self.__table_memo_index.rowCount()

            brief = row['brief']
            content = row['content']
            text = brief if str_available(brief) else content
            # https://stackoverflow.com/a/2873416/12929244
            self.__table_memo_index.AppendRow([datetime2text(row['time']), text[:30] + (text[30:] and '...')], index)
            self.__table_memo_index.item(row_index, 0).setData(Qt.UserRole, index)

    def create_new_memo(self, _time: datetime.datetime):
        self.__table_memo_index.clearSelection()
        if _time is not None:
            self.__datetime_time.setDateTime(_time)
        self.__line_brief.setText('')
        self.__text_record.setText('')
        self.__current_index = None

    def load_edit_memo(self, index: int):
        """
        The index should exist in left memo list
        :param index:
        :return:
        """
        df = self.__current_memos
        if df is None or df.empty:
            self.create_new_memo()
            return

        s = df.loc[index]
        if len(s) == 0:
            self.create_new_memo()
            return

        self.__current_index = index

        _time = s['time']
        brief = s['brief']
        content = s['content']

        self.__datetime_time.setDateTime(to_py_datetime(_time))
        self.__line_brief.setText(brief)
        self.__text_record.setText(content)

    # def update_memo_content(self, index: int):
    #     for row in range(0, self.__table_memo_index.rowCount()):
    #         table_item = self.__table_memo_index.item(row, 0)
    #         row_index = table_item.data(Qt.UserRole)
    #         if row_index == index:
    #             self.__table_memo_index.selectRow(row)
    #             break

    # def select_stock(self, stock_identity: str):
    #     index = self.__combo_stock.findData(stock_identity)
    #     if index != -1:
    #         print('Select combox index: %s' % index)
    #         self.__combo_stock.setCurrentIndex(index)
    #     else:
    #         print('No index in combox for %s' % stock_identity)
    #         self.__combo_stock.setCurrentIndex(-1)
    #         self.__load_stock_memo(stock_identity)

    # def select_memo_by_index(self, index: int):
    #     for row in range(0, self.__table_memo_index.rowCount()):
    #         table_item = self.__table_memo_index.item(row, 0)
    #         row_index = table_item.data(Qt.UserRole)
    #         if row_index == index:
    #             self.__table_memo_index.selectRow(row)
    #             break

    # -------------------------------------------------------------------

    # def __load_stock_memo(self, stock_identity: str):
    #     print('Load stock memo for %s' % stock_identity)
    #
    #     self.__table_memo_index.clear()
    #     self.__table_memo_index.setRowCount(0)
    #     self.__table_memo_index.setHorizontalHeaderLabels(['时间', '摘要'])
    #
    #     self.__current_stock = stock_identity
    #     self.__current_index = None
    #
    #     # if self.__memo_recordset is None or \
    #     #         self.__current_stock is None or self.__current_stock == '':
    #     #     return
    #     #
    #     # self.__current_record = self.__memo_recordset.get_record(stock_identity)
    #     # df = self.__current_record.get_records('memo')
    #
    #     self.__current_select = self.__memo_record.get_records({'security': stock_identity})
    #
    #     select_index = None
    #     for index, row in self.__current_select.iterrows():
    #         if select_index is None:
    #             select_index = index
    #         self.__table_memo_index.AppendRow([datetime2text(row['time']), row['brief']], index)
    #     self.select_memo_by_index(select_index)
    #
    # def __reload_stock_memo(self):
    #     self.__line_brief.setText('')
    #     self.__text_record.setText('')
    #     self.__table_memo_index.clear()
    #     self.__table_memo_index.setRowCount(0)
    #     self.__table_memo_index.setHorizontalHeaderLabels(['时间', '摘要'])
    #
    #     if self.__current_record is None:
    #         print('Warning: Current record is None, cannot reload.')
    #         return
    #     df = self.__current_record.get_records('memo')
    #
    #     select_index = self.__current_index
    #     for index, row in df.iterrows():
    #         if select_index is None:
    #             select_index = index
    #         self.__table_memo_index.AppendRow([datetime2text(row['time']), row['brief']], index)
    #     self.select_memo_by_index(select_index)
    #
    # def __load_memo_by_index(self, index: int):
    #     self.__table_memo_index.clearSelection()
    #     if self.__current_record is None or index is None:
    #         return
    #
    #     df = self.__current_record.get_records('memo')
    #     s = df.loc[index]
    #     if len(s) == 0:
    #         return
    #     self.__current_index = index
    #
    #     _time = s['time']
    #     brief = s['brief']
    #     content = s['content']
    #
    #     self.__datetime_time.setDateTime(to_py_datetime(_time))
    #     self.__line_brief.setText(brief)
    #     self.__text_record.setText(content)


# ----------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------ class StockHistoryUi ------------------------------------------------
# ---------------------------------------------  The Candle Stick Interface --------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

class StockHistoryUi(QWidget):
    ADJUST_TAIL = 0
    ADJUST_HEAD = 1
    ADJUST_NONE = 2

    RETURN_LOG = 3
    RETURN_SIMPLE = 4

    def __init__(self, memo_data: StockMemoData):
        self.__memo_data = memo_data
        super(StockHistoryUi, self).__init__()

        self.__sas = memo_data.get_sas()
        self.__memo_record: StockMemoRecord = memo_data.get_memo_record()

        self.__paint_securities = ''
        self.__paint_trade_data = None

        # # Record
        # user_path = os.path.expanduser('~')
        # project_path = sas.get_project_path() if sas is not None else os.getcwd()
        #
        # self.__root_path = \
        #     memo_path_from_project_path(project_path) if user_path == '' else \
        #     memo_path_from_user_path(user_path)
        # self.__memo_record = Record(os.path.join(self.__root_path, 'stock_memo.csv'), STOCK_MEMO_COLUMNS)

        # vnpy chart
        self.__vnpy_chart = ChartWidget()

        # Memo editor
        self.__memo_editor: StockMemoEditor = self.__memo_data.get_data('editor')
        self.__memo_editor.add_observer(self)

        # Timer for workaround signal fired twice
        self.__accepted = False
        self.__timer = QTimer()
        self.__timer.setInterval(1000)
        self.__timer.timeout.connect(self.on_timer)
        self.__timer.start()

        # Ui component
        data_utility = self.__sas.get_data_hub_entry().get_data_utility() if self.__sas is not None else None
        self.__combo_name = SecuritiesSelector(data_utility)
        self.__button_ensure = QPushButton('确定')

        self.__check_abs = QCheckBox('固定价格范围')
        self.__check_memo = QCheckBox('笔记')
        self.__check_volume = QCheckBox('成交量')

        self.__radio_adj_tail = QRadioButton('后复权')
        self.__radio_adj_head = QRadioButton('前复权')
        self.__radio_adj_none = QRadioButton('不复权')
        self.__group_adj = QButtonGroup(self)

        self.__radio_log_return = QRadioButton('对数收益')
        self.__radio_simple_return = QRadioButton('算术收益')
        self.__group_return = QButtonGroup(self)

        self.__init_ui()
        self.__config_ui()

    def __init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.__group_adj.addButton(self.__radio_adj_tail)
        self.__group_adj.addButton(self.__radio_adj_head)
        self.__group_adj.addButton(self.__radio_adj_none)
        group_box_adj, group_layout = create_h_group_box('')
        group_layout.addWidget(self.__radio_adj_tail)
        group_layout.addWidget(self.__radio_adj_head)
        group_layout.addWidget(self.__radio_adj_none)

        self.__group_return.addButton(self.__radio_log_return)
        self.__group_return.addButton(self.__radio_simple_return)
        group_box_return, group_layout = create_h_group_box('')
        group_layout.addWidget(self.__radio_log_return)
        group_layout.addWidget(self.__radio_simple_return)

        group_box, group_layout = create_v_group_box('Securities')

        main_layout.addWidget(self.__vnpy_chart, 99)
        main_layout.addWidget(group_box)

        group_layout.addLayout(horizon_layout([
            self.__combo_name, group_box_adj, group_box_return, self.__button_ensure,
            self.__check_abs, self.__check_volume, self.__check_memo
        ]))

    def __config_ui(self):
        data_utility = self.__sas.get_data_hub_entry().get_data_utility()
        index_dict = data_utility.get_support_index()

        self.__combo_name.setEditable(True)
        for key in index_dict:
            self.__combo_name.addItem(key + ' | ' + index_dict.get(key), key)

        self.__radio_adj_none.setChecked(True)
        self.__radio_simple_return.setChecked(True)

        self.__check_abs.clicked.connect(self.on_button_abs)
        self.__check_memo.clicked.connect(self.on_button_memo)
        self.__check_volume.clicked.connect(self.on_button_volume)
        self.__button_ensure.clicked.connect(self.on_button_ensure)

        self.setMinimumWidth(1280)
        self.setMinimumHeight(800)

        # --------------------- Editor ----------------------

        # self.__memo_editor.closeEvent = self.on_editor_closed

        # ---------------------- Chart ----------------------

        self.__vnpy_chart.add_plot("candle", hide_x_axis=True)
        self.__vnpy_chart.add_plot("volume", maximum_height=200)
        self.__vnpy_chart.add_plot("memo", maximum_height=50)

        self.__vnpy_chart.add_item(CandleItem, "candle", "candle")
        self.__vnpy_chart.add_item(VolumeItem, "volume", "volume")
        self.__vnpy_chart.add_item(MemoItem, "memo", "memo")

        self.__vnpy_chart.add_cursor()
        self.__vnpy_chart.scene().sigMouseClicked.connect(self.on_chart_clicked)

    @pyqtSlot(MouseClickEvent)
    def on_chart_clicked(self, event: MouseClickEvent):
        if not event.double or self.__accepted:
            return
        self.__accepted = True
        scene_pt = event.scenePos()
        items = self.__vnpy_chart.scene().items(scene_pt)
        for i in items:
            if isinstance(i, pg.PlotItem):
                view = i.getViewBox()
                view_pt = view.mapSceneToView(scene_pt)
                self.popup_memo_editor(view_pt.x())
                break
        # print("Plots:" + str([x for x in items if isinstance(x, pg.PlotItem)]))

    def on_timer(self):
        # Workaround for click event double fire
        self.__accepted = False

    def on_button_abs(self):
        enable = self.__check_abs.isChecked()
        self.__vnpy_chart.get_item('candle').set_y_range_dynamic(not enable)
        self.__vnpy_chart.refresh_history()
        self.__vnpy_chart.update()

    def on_button_memo(self):
        # enable = self.__check_memo.isChecked()
        # self.__vnpy_chart.enable_item('memo', enable)
        pass

    def on_button_volume(self):
        # enable = self.__check_volume.isChecked()
        # self.__vnpy_chart.enable_item('volume', enable)
        pass

    def on_button_ensure(self):
        input_securities = self.__combo_name.currentText()
        if '|' in input_securities:
            input_securities = input_securities.split('|')[0].strip()
        self.show_security(input_securities)

    # ------------------- Interface of StockMemoEditor.Observer ------------------

    def on_memo_updated(self):
        self.load_security_memo()
        self.__vnpy_chart.refresh_history()

    # ----------------------------------------------------------------------------

    def show_security(self, security: str, check_update: bool = False):
        if self.__radio_adj_tail.isChecked():
            adjust_method = StockHistoryUi.ADJUST_TAIL
        elif self.__radio_adj_head.isChecked():
            adjust_method = StockHistoryUi.ADJUST_HEAD
        elif self.__radio_adj_none.isChecked():
            adjust_method = StockHistoryUi.ADJUST_NONE
        else:
            adjust_method = StockHistoryUi.ADJUST_NONE

        if self.__radio_log_return.isChecked():
            return_style = StockHistoryUi.RETURN_LOG
        elif self.__radio_simple_return.isChecked():
            return_style = StockHistoryUi.RETURN_SIMPLE
        else:
            return_style = StockHistoryUi.RETURN_SIMPLE

        if not self.load_security_data(security, adjust_method, return_style, check_update):
            QMessageBox.information(self,
                                    QtCore.QCoreApplication.translate('History', '没有数据'),
                                    QtCore.QCoreApplication.translate('History', '没有交易数据，请检查证券编码或更新本地数据'),
                                    QMessageBox.Ok, QMessageBox.Ok)
        else:
            self.load_security_memo()
            self.__vnpy_chart.refresh_history()

    def popup_memo_editor(self, ix: float):
        bar_data = self.__vnpy_chart.get_bar_manager().get_bar(ix)
        if bar_data is not None:
            _time = bar_data.datetime.to_pydatetime()
            self.popup_memo_editor_by_time(_time)
        else:
            self.popup_memo_editor_by_time(now())

    def popup_memo_editor_by_time(self, _time: datetime):
        self.__memo_editor.select_security(self.__paint_securities)
        self.__memo_editor.select_memo_by_day(_time)
        # self.__memo_editor.show()
        self.__memo_editor.exec()

    def load_security_data(self, securities: str, adjust_method: int, return_style: int,
                           check_update: bool = False) -> bool:
        data_utility = self.__sas.get_data_hub_entry().get_data_utility()
        index_dict = data_utility.get_support_index()

        if securities != self.__paint_securities or self.__paint_trade_data is None:
            if securities in index_dict.keys():
                uri = 'TradeData.Index.Daily'
            else:
                uri = 'TradeData.Stock.Daily'
            # if check_update:
            #     self.__sas.get_data_hub_entry().get_data_utility().check_update(uri, securities)
            trade_data = self.__sas.get_data_hub_entry().get_data_center().query(uri, securities)

            # base_path = os.path.dirname(os.path.abspath(__file__))
            # history_path = os.path.join(base_path, 'History')
            # depot_path = os.path.join(history_path, 'depot')
            # his_file = os.path.join(depot_path, securities + '.his')

            # self.__memo_file = his_file
            self.__paint_trade_data = trade_data
            self.__paint_securities = securities

        if self.__paint_trade_data is None or len(self.__paint_trade_data) == 0:
            return False

        trade_data = pd.DataFrame()
        if adjust_method == StockHistoryUi.ADJUST_TAIL and 'adj_factor' in self.__paint_trade_data.columns:
            trade_data['open'] = self.__paint_trade_data['open'] * self.__paint_trade_data['adj_factor']
            trade_data['close'] = self.__paint_trade_data['close'] * self.__paint_trade_data['adj_factor']
            trade_data['high'] = self.__paint_trade_data['high'] * self.__paint_trade_data['adj_factor']
            trade_data['low'] = self.__paint_trade_data['low'] * self.__paint_trade_data['adj_factor']
        elif adjust_method == StockHistoryUi.ADJUST_HEAD and 'adj_factor' in self.__paint_trade_data.columns:
            trade_data['open'] = self.__paint_trade_data['open'] / self.__paint_trade_data['adj_factor']
            trade_data['close'] = self.__paint_trade_data['close'] / self.__paint_trade_data['adj_factor']
            trade_data['high'] = self.__paint_trade_data['high'] / self.__paint_trade_data['adj_factor']
            trade_data['low'] = self.__paint_trade_data['low'] / self.__paint_trade_data['adj_factor']
        else:
            trade_data['open'] = self.__paint_trade_data['open']
            trade_data['close'] = self.__paint_trade_data['close']
            trade_data['high'] = self.__paint_trade_data['high']
            trade_data['low'] = self.__paint_trade_data['low']
        trade_data['amount'] = self.__paint_trade_data['amount']
        trade_data['trade_date'] = pd.to_datetime(self.__paint_trade_data['trade_date'])

        if return_style == StockHistoryUi.RETURN_LOG:
            trade_data['open'] = np.log(trade_data['open'])
            trade_data['close'] = np.log( trade_data['close'])
            trade_data['high'] = np.log(trade_data['high'])
            trade_data['low'] = np.log(trade_data['low'])

        bars = self.df_to_bar_data(trade_data, securities)
        self.__vnpy_chart.get_bar_manager().clear_all()
        self.__vnpy_chart.get_bar_manager().update_history(bars)

        return True

    def load_security_memo(self) -> bool:
        self.__combo_name.select_security(self.__paint_securities, True)

        memo_record = self.__memo_record.get_stock_memos(self.__paint_securities)
        bar_manager = self.__vnpy_chart.get_bar_manager()

        if memo_record is None or bar_manager is None:
            return False

        try:
            memo_df = memo_record.copy()
            memo_df['normalised_time'] = memo_df['time'].dt.normalize()
            memo_df_grouped = memo_df.groupby('normalised_time')
        except Exception as e:
            return False
        finally:
            pass

        append_items = []
        max_memo_count = 0
        for group_time, group_df in memo_df_grouped:
            memo_count = len(group_df)
            max_memo_count = max(memo_count, max_memo_count)
            if not bar_manager.set_item_data(group_time, 'memo', group_df):
                bar = BarData(datetime=group_time,
                              exchange=Exchange.SSE,
                              symbol=self.__paint_securities)
                bar.extra = {'memo': group_df}
                append_items.append(bar)
        bar_manager.set_item_data_range('memo', 0.0, max_memo_count)
        bar_manager.update_history(append_items)

        # memo_item = self.__vnpy_chart.get_item('memo')
        # if memo_item is not None:
        #     memo_item.refresh_history()
        # self.__vnpy_chart.update_history()

        return True

    # TODO: Move it to common place
    @staticmethod
    def df_to_bar_data(df: pd.DataFrame, securities: str, exchange: Exchange = Exchange.SSE) -> [BarData]:
        # 98 ms
        bars = []
        for trade_date, amount, open, close, high, low in \
                zip(df['trade_date'], df['amount'], df['open'], df['close'], df['high'], df['low']):
            bar = BarData(datetime=trade_date,
                          exchange=exchange,
                          symbol=securities)

            bar.interval = Interval.DAILY
            bar.volume = amount * 10000
            bar.open_interest = 0
            bar.open_price = open
            bar.high_price = high
            bar.low_price = low
            bar.close_price = close
            bars.append(bar)
        return bars

    # @staticmethod
    # def df_to_bar_data1(df: pd.DataFrame) -> [BarData]:
    #     # 3488 ms
    #     bars = []
    #     for index, row in df.iterrows():
    #         date_time = row['trade_date']
    #         bar = BarData(datetime=date_time,
    #                       exchange=Exchange.SSE,
    #                       symbol='000001')
    #
    #         bar.interval = Interval.DAILY
    #         bar.volume = row['amount'] * 10000
    #         bar.open_interest = row['open']
    #         bar.open_price = row['open']
    #         bar.high_price = row['high']
    #         bar.low_price = row['low']
    #         bar.close_price = row['close']
    #         bars.append(bar)
    #     return bars


# ----------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------ Main UI -------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

NOTE = '''Stock Memo说明
1.Stock Memo相关的数据作为个人数据默认保存到系统用户目录下，更新程序不会破坏数据
2.如果用户自己指定保存目录，请手动复制已存在的文件到新目录下'''


# ------------------------------------------------ Memo Extra Interface ------------------------------------------------

class MemoExtra:
    def __init__(self):
        self.__memo_ui = None

    def set_memo_ui(self, memo_ui):
        self.__memo_ui = memo_ui

    def notify_memo_ui_update(self):
        self.__memo_ui.update_list()

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


# -------------------------------------------------- class StockMemo ---------------------------------------------------

class StockMemo(QWidget):
    STATIC_HEADER = ['Security']

    def __init__(self, memo_data: StockMemoData):
        super(StockMemo, self).__init__()
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
        return StockMemo.STATIC_HEADER + [memo_extra.title_text() for memo_extra in self.__memo_extras]


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
        self.__memo_history = StockHistoryUi(self.__memo_data)
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
        self.notify_memo_ui_update()

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

    memo_ui = StockMemo(memoData)
    memo_ui.add_memo_extra(MemoExtra_MemoContent(memoData))
    memo_ui.add_memo_extra(MemoExtra_MemoHistory(memoData))
    memo_ui.add_memo_extra(MemoExtra_StockTags(memoData))
    memo_ui.update_list()

    return memo_ui, {'name': '股票笔记', 'show': False}


# ------------------------------------------------ File Entry : main() -------------------------------------------------

def main():
    app = QApplication(sys.argv)
    # dlg = WrapperQDialog(StockMemoEditor(None, None))
    
    stock_memo = StockMemo(None)
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




















