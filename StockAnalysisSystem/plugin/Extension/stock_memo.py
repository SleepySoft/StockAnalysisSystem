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
    QMessageBox, QWidget, QComboBox, QCheckBox, QRadioButton, QLineEdit, QAbstractItemView
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent

from StockAnalysisSystem.porting.vnpy_chart import *
from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.ui_utility import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem
from StockAnalysisSystem.core.Utiltity.securities_selector import SecuritiesSelector


def memo_path_from_project_path(project_path: str) -> str:
    memo_path = os.path.join(project_path, 'Data', 'StockMemo')
    try:
        os.makedirs(memo_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            print('Build memo path: %s FAIL' % memo_path)
    finally:
        return memo_path


class Record:
    RECORD_COLUMNS = ['time', 'brief', 'content', 'classify']

    def __init__(self, record_path: str):
        self.__record_path = record_path
        self.__record_sheet = pd.DataFrame(columns=Record.RECORD_COLUMNS)

    def is_empty(self) -> bool:
        return self.__record_sheet is None or len(self.__record_sheet) == 0

    def add_record(self, _time: datetime, brief: str, content: str, classify: str, _save: bool = True) -> (bool, int):
        if not self.__check_record_format(_time, brief, content):
            print('add_record() format error.')
            return False
        df = self.__record_sheet
        max_index = max(df.index) if len(df) > 0 else 0
        new_index = max_index + 1
        df.loc[new_index, ['time', 'brief', 'content', 'classify']] = ([_time, brief, content, classify])
        return (self.save() if _save and self.save() else True), new_index

    def update_record(self, index, _time: datetime.datetime, brief: str, content: str, _save: bool = True) -> bool:
        if not self.__check_record_format(_time, brief, content):
            print('update_record() format error.')
            return False
        df = self.__record_sheet
        if index in df.index.values:
            df.loc[index, ['time', 'brief', 'content']] = ([_time, brief, content])
        else:
            print('Warning: Index %s not in record.' % str(index))
        return self.save() if _save else True

    def get_records(self, classify: str = '') -> pd.DataFrame:
        if len(self.__record_sheet) == 0 or not str_available(classify):
            return self.__record_sheet
        return self.__record_sheet[self.__record_sheet['classify'] == classify]

    def del_records(self, idx: int or [int]):
        self.__record_sheet.drop(idx)

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
            df['time'] = pd.to_datetime(df['time'], infer_datetime_format=True)
            df.reindex()
            self.__record_sheet = df
            return set(Record.RECORD_COLUMNS).issubset(self.__record_sheet.columns)
        except Exception as e:
            return False
        finally:
            pass

    def __save(self, record_path: str) -> bool:
        try:
            self.__record_sheet = self.__record_sheet[Record.RECORD_COLUMNS]
            self.__record_sheet.to_csv(record_path)
            return True
        except Exception as e:
            print('Save stock memo %s error.' % record_path)
            print(e)
            return False
        finally:
            pass

    @staticmethod
    def __check_record_format(_time: datetime.datetime, brief: str, content: str):
        return isinstance(_time, datetime.datetime) and isinstance(brief, str) and isinstance(content, str)


class RecordSet:
    def __init__(self, record_root: str):
        self.__record_root = record_root
        self.__record_depot = {}

    def set_record_root(self, memo_root: str):
        self.__record_root = memo_root

    def get_record_root(self) -> str:
        return self.__record_root

    def get_record(self, record_name: str):
        record = self.__record_depot.get(record_name, None)
        if record is None:
            record = Record(self.__get_record_file_path(record_name))
            record.load()
            self.__record_depot[record_name] = record
        else:
            print('Get cached record for %s' % record_name)
        return record

    def get_exists_record_name(self) -> []:
        return self.__enumerate_record()

    def __get_record_file_path(self, record_name: str) -> str:
        return os.path.join(self.__record_root, record_name + '.csv')

    def __enumerate_record(self) -> list:
        records = []
        for parent, dirnames, filenames in os.walk(self.__record_root):
            for filename in filenames:
                if filename.endswith('.csv'):
                    records.append(filename[:-4])
        return records


class StockMemoEditor(QDialog):
    def __init__(self, sas: StockAnalysisSystem, memo_record: RecordSet, parent: QWidget = None):
        super(StockMemoEditor, self).__init__(parent)

        self.__sas = sas
        self.__memo_recordset = memo_record

        self.__current_stock = None
        self.__current_index = None
        self.__current_record: Record = None

        data_utility = self.__sas.get_data_hub_entry().get_data_utility() if self.__sas is not None else None
        self.__combo_stock = SecuritiesSelector(data_utility)
        self.__table_memo_index = EasyQTableWidget()

        self.__datetime_time = QDateTimeEdit(QDateTime().currentDateTime())
        self.__line_brief = QLineEdit()
        self.__text_record = QTextEdit()

        self.__button_new = QPushButton('新建')
        self.__button_apply = QPushButton('保存')

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
        group_layout.addLayout(horizon_layout([QLabel('时间：'), self.__datetime_time, self.__button_new], [1, 99, 1]))
        group_layout.addLayout(horizon_layout([QLabel('摘要：'), self.__line_brief], [1, 99]))
        group_layout.addWidget(self.__text_record)
        group_layout.addLayout(horizon_layout([QLabel(''), self.__button_apply], [99, 1]))
        root_layout.addWidget(group_box, 6)

        self.setMinimumSize(500, 600)

    def config_ui(self):
        self.setWindowTitle('笔记编辑器')
        self.__datetime_time.setCalendarPopup(True)

        self.__combo_stock.setEditable(False)
        self.__combo_stock.currentIndexChanged.connect(self.on_combo_select_changed)

        self.__table_memo_index.insertColumn(0)
        self.__table_memo_index.insertColumn(0)
        self.__table_memo_index.setHorizontalHeaderLabels(['时间', '摘要'])
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
        if self.__current_stock is None:
            QMessageBox.information(self, '错误', '请选择需要做笔记的股票', QMessageBox.Ok, QMessageBox.Ok)
        self.create_new_memo(None)

    def on_button_apply(self):
        _time = self.__datetime_time.dateTime().toPyDateTime()
        brief = self.__line_brief.text()
        content = self.__text_record.toPlainText()

        if not str_available(brief):
            QMessageBox.information(self, '错误', '请至少填写笔记摘要', QMessageBox.Ok, QMessageBox.Ok)
            return

        if self.__current_index is not None:
            ret = self.__current_record.update_record(self.__current_index, _time, brief, content, True)
        else:
            ret, index = self.__current_record.add_record(_time, brief, content, 'memo', True)
            self.__current_index = index
        if ret:
            self.__reload_stock_memo()

    def on_combo_select_changed(self):
        input_securities = self.__combo_stock.get_input_securities()
        self.__load_stock_memo(input_securities)

    def on_table_selection_changed(self):
        if self.__current_record is None:
            return
        sel_index = self.__table_memo_index.GetCurrentIndex()
        if sel_index < 0:
            return
        sel_item = self.__table_memo_index.item(sel_index, 0)
        if item is None:
            return
        df_index = sel_item.data(Qt.UserRole)
        self.__load_memo_by_index(df_index)

    def select_stock(self, stock_identity: str):
        index = self.__combo_stock.findData(stock_identity)
        if index != -1:
            print('Select combox index: %s' % index)
            self.__combo_stock.setCurrentIndex(index)
        else:
            print('No index in combox for %s' % stock_identity)
            self.__load_stock_memo(stock_identity)

    def select_memo_by_time(self, _time: datetime.datetime):
        if self.__current_record is None or self.__current_record.is_empty():
            self.create_new_memo(_time)
            return

        df = self.__current_record.get_records('memo')
        time_serial = df['time'].dt.normalize()
        select_df = df[time_serial == _time.replace(hour=0, minute=0, second=0, microsecond=0)]

        select_index = None
        for index, row in select_df.iterrows():
            select_index = index
            break

        if select_index is not None:
            self.select_memo_by_index(select_index)
        else:
            self.create_new_memo(_time)

    def select_memo_by_index(self, index: int):
        for row in range(0, self.__table_memo_index.rowCount()):
            table_item = self.__table_memo_index.item(row, 0)
            row_index = table_item.data(Qt.UserRole)
            if row_index == index:
                self.__table_memo_index.selectRow(row)
                break

    def create_new_memo(self, _time: datetime.datetime):
        self.__table_memo_index.clearSelection()
        if _time is not None:
            self.__datetime_time.setDateTime(_time)
        self.__line_brief.setText('')
        self.__text_record.setText('')
        self.__current_index = None

    # -------------------------------------------------------------------

    def __load_stock_memo(self, stock_identity: str):
        print('Load stock memo for %s' % stock_identity)

        self.__table_memo_index.clear()
        self.__table_memo_index.setRowCount(0)
        self.__table_memo_index.setHorizontalHeaderLabels(['时间', '摘要'])

        self.__current_stock = stock_identity
        self.__current_record = None
        self.__current_index = None

        if self.__memo_recordset is None or \
                self.__current_stock is None or self.__current_stock == '':
            return

        self.__current_record = self.__memo_recordset.get_record(stock_identity)
        df = self.__current_record.get_records('memo')

        select_index = None
        for index, row in df.iterrows():
            if select_index is None:
                select_index = index
            self.__table_memo_index.AppendRow([datetime2text(row['time']), row['brief']], index)
        self.select_memo_by_index(select_index)

    def __reload_stock_memo(self):
        self.__line_brief.setText('')
        self.__text_record.setText('')
        self.__table_memo_index.clear()
        self.__table_memo_index.setRowCount(0)
        self.__table_memo_index.setHorizontalHeaderLabels(['时间', '摘要'])

        if self.__current_record is None:
            print('Warning: Current record is None, cannot reload.')
            return
        df = self.__current_record.get_records('memo')

        select_index = self.__current_index
        for index, row in df.iterrows():
            if select_index is None:
                select_index = index
            self.__table_memo_index.AppendRow([datetime2text(row['time']), row['brief']], index)
        self.select_memo_by_index(select_index)

    def __load_memo_by_index(self, index: int):
        self.__table_memo_index.clearSelection()
        if self.__current_record is None or index is None:
            return

        df = self.__current_record.get_records('memo')
        s = df.loc[index]
        if len(s) == 0:
            return
        self.__current_index = index

        _time = s['time']
        brief = s['brief']
        content = s['content']

        self.__datetime_time.setDateTime(to_py_datetime(_time))
        self.__line_brief.setText(brief)
        self.__text_record.setText(content)


# ----------------------------------------------------------------------------------------------------------------------

class StockHistoryUi(QWidget):
    ADJUST_TAIL = 0
    ADJUST_HEAD = 1
    ADJUST_NONE = 2

    RETURN_LOG = 3
    RETURN_SIMPLE = 4

    def __init__(self, sas: StockAnalysisSystem):
        super(StockHistoryUi, self).__init__()

        self.__sas = sas
        self.__paint_securities = ''
        self.__paint_trade_data = None

        # Record set
        project_path = sas.get_project_path() if sas is not None else os.getcwd()
        self.__root_path = memo_path_from_project_path(project_path)
        self.__memo_recordset = RecordSet(self.__root_path)

        # vnpy chart
        self.__vnpy_chart = ChartWidget()

        # Memo editor
        self.__memo_editor = StockMemoEditor(self.__sas, self.__memo_recordset)

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
            self.__check_volume, self.__check_memo
        ]))

    def __config_ui(self):
        data_utility = self.__sas.get_data_hub_entry().get_data_utility()
        index_dict = data_utility.get_support_index()

        self.__combo_name.setEditable(True)
        for key in index_dict:
            self.__combo_name.addItem(key + ' | ' + index_dict.get(key), key)

        self.__radio_adj_none.setChecked(True)
        self.__radio_simple_return.setChecked(True)

        self.__check_memo.clicked.connect(self.on_button_memo)
        self.__check_volume.clicked.connect(self.on_button_volume)
        self.__button_ensure.clicked.connect(self.on_button_ensure)

        self.setMinimumWidth(1280)
        self.setMinimumHeight(800)

        # --------------------- Editor ----------------------

        self.__memo_editor.closeEvent = self.on_editor_closed

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

    def on_button_memo(self):
        enable = self.__check_memo.isChecked()

    def on_button_volume(self):
        enable = self.on_button_volume.isChecked()

    def on_button_ensure(self):
        input_securities = self.__combo_name.currentText()
        if '|' in input_securities:
            input_securities = input_securities.split('|')[0].strip()

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

        if not self.load_security_data(input_securities, adjust_method, return_style):
            QMessageBox.information(self,
                                    QtCore.QCoreApplication.translate('History', '没有数据'),
                                    QtCore.QCoreApplication.translate('History', '没有交易数据，请检查证券编码或更新本地数据'),
                                    QMessageBox.Ok, QMessageBox.Ok)
        else:
            self.load_security_memo()
            self.__vnpy_chart.refresh_history()

    def on_editor_closed(self, event):
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
        self.__memo_editor.select_memo_by_time(_time)
        # self.__memo_editor.show()
        self.__memo_editor.exec()

    def load_security_data(self, securities: str, adjust_method: int, return_style: int) -> bool:
        data_utility = self.__sas.get_data_hub_entry().get_data_utility()
        index_dict = data_utility.get_support_index()

        if securities != self.__paint_securities or self.__paint_trade_data is None:
            if securities in index_dict.keys():
                uri = 'TradeData.Index.Daily'
            else:
                uri = 'TradeData.Stock.Daily'
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
        self.__vnpy_chart.get_bar_manager().update_history(bars)

        return True

    def load_security_memo(self) -> bool:
        self.__memo_editor.select_stock(self.__paint_securities)

        memo_record = self.__memo_recordset.get_record(self.__paint_securities)
        bar_manager = self.__vnpy_chart.get_bar_manager()

        if memo_record is None or bar_manager is None:
            return False

        try:
            memo_df = memo_record.get_records().copy()
            memo_df['normalised_time'] = memo_df['time'].dt.normalize()
            memo_df_grouped = memo_df.groupby('normalised_time')
        except Exception as e:
            return False
        finally:
            pass

        max_memo_count = 0
        for group_time, group_df in memo_df_grouped:
            memo_count = len(group_df)
            max_memo_count = max(memo_count, max_memo_count)
            bar_manager.set_item_data(group_time, 'memo', group_df)
        bar_manager.set_item_data_range('memo', 0.0, max_memo_count)

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


def init(sas: StockAnalysisSystem) -> bool:
    try:
        global sasEntry
        sasEntry = sas
    except Exception as e:
        print(e)
        return False
    finally:
        pass
    return True


def widget(parent: QWidget) -> (QWidget, dict):
    return StockHistoryUi(sasEntry), {'name': '股票笔记', 'show': False}


# ------------------------------------------------ File Entry : main() -------------------------------------------------

def main():
    app = QApplication(sys.argv)
    dlg = WrapperQDialog(StockMemoEditor(None, None))
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




















