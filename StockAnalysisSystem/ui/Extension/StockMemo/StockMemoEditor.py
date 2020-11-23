import os
import errno

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QTimer, QDateTime, QPoint, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QButtonGroup, QDateTimeEdit, QApplication, QLabel, QTextEdit, QPushButton, QVBoxLayout, \
    QMessageBox, QWidget, QComboBox, QCheckBox, QRadioButton, QLineEdit, QAbstractItemView, QFileDialog, QDialog
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent

from StockAnalysisSystem.core.Utiltity.common import *
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


# ----------------------------------------------- class StockMemoEditor ------------------------------------------------

class StockMemoEditor(QDialog):
    LIST_HEADER = ['Time', 'Preview']

    # class Observer:
    #     def __init__(self):
    #         pass
    #
    #     def on_memo_updated(self):
    #         pass

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
        self.__button_delete = QPushButton('Delete')

        self.init_ui()
        self.config_ui()

    def init_ui(self):
        root_layout = QHBoxLayout()
        self.setLayout(root_layout)

        group_box, group_layout = create_v_group_box('')
        group_layout.addWidget(self.__combo_stock, 1)
        group_layout.addWidget(self.__table_memo_index, 99)
        group_layout.addWidget(self.__button_delete, 1)
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
        self.__button_delete.clicked.connect(self.on_button_delete)

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
        # self.__trigger_memo_updated()

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

        # self.__trigger_memo_updated()
        self.__memo_data.broadcast_data_updated('memo_record')

    def on_button_delete(self):
        if self.__current_index is not None:
            self.__memo_record.del_records(self.__current_index)
            self.__memo_record.save()
            self.load_security_memo(self.__current_stock)
            self.update_memo_list()
            self.__memo_data.broadcast_data_updated('memo_record')

    def on_combo_select_changed(self):
        input_securities = self.__combo_stock.get_input_securities()
        if input_securities != self.__current_stock:
            self.load_security_memo(input_securities)

    def on_table_selection_changed(self):
        sel_index = self.__table_memo_index.GetCurrentIndex()
        if sel_index < 0:
            return
        sel_item = self.__table_memo_index.item(sel_index, 0)
        if sel_item is None:
            return
        df_index = sel_item.data(Qt.UserRole)
        self.load_edit_memo(df_index)

    # --------------------------------------------------------------------------------------------

    # def add_observer(self, ob: Observer):
    #     self.__observers.append(ob)
    #
    # def __trigger_memo_updated(self):
    #     for ob in self.__observers:
    #         ob.on_memo_updated()

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

        self.__current_index = None
        self.__enter_new_mode()

    def create_new_memo(self, _time: datetime.datetime or None):
        self.__table_memo_index.clearSelection()
        if _time is not None:
            self.__datetime_time.setDateTime(_time)
        self.__line_brief.setText('')
        self.__text_record.setText('')
        self.__current_index = None
        self.__enter_new_mode()

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
        self.__line_brief.setText(str(brief))
        self.__text_record.setText(str(content))
        self.__enter_edit_mode()
        
    def __enter_new_mode(self):
        self.__button_new.setText('New *')

    def __enter_edit_mode(self):
        self.__button_new.setText('New')

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






