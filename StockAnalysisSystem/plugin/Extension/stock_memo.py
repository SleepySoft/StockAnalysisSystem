import sys
import datetime
import traceback
import numpy as np
import pandas as pd
from os import path

from PyQt5 import QtCore
from PyQt5.QtCore import QTimer, QDateTime, QPoint
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QButtonGroup, QDateTimeEdit, QApplication, QLabel, QTextEdit, QPushButton, QVBoxLayout, \
    QMessageBox, QWidget, QComboBox, QCheckBox, QRadioButton

from StockAnalysisSystem.porting.vnpy_chart import *
from StockAnalysisSystem.core.Utiltity.ui_utility import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem


# class StockMemoEditor(QDialog):
#     def __init__(self):
#         super(StockMemoEditor, self).__init__()
#
#         self.__source = ''
#         self.__current_record = None
#
#         self.__label_uuid = QLabel()
#         self.__label_source = QLabel()
#         self.__text_record = QTextEdit()
#         self.__datetime_time = QDateTimeEdit(QDateTime.currentDateTime())
#
#         self.__button_apply = QPushButton('保存')
#         self.__button_cancel = QPushButton('取消')
#
#         self.init_ui()
#         self.config_ui()
#
#     def init_ui(self):
#         root_layout = QVBoxLayout()
#         self.setLayout(root_layout)
#
#         group_box, group_layout = create_v_group_box('')
#         group_layout.addWidget(self.__label_uuid)
#         group_layout.addWidget(self.__label_source)
#         group_layout.addWidget(self.__datetime_time)
#         # group_layout.addLayout(horizon_layout([QLabel('笔记ID'), self.__label_uuid]))
#         # group_layout.addLayout(horizon_layout([QLabel('笔记文件'), self.__label_source]))
#         # group_layout.addLayout(horizon_layout([QLabel('记录时间'), self.__datetime_time]))
#
#         root_layout.addWidget(group_box, 0)
#         root_layout.addWidget(self.__text_record, 10)
#
#         root_layout.addLayout(horizon_layout([self.__button_apply, self.__button_cancel]))
#
#         self.setMinimumSize(500, 600)
#
#     def config_ui(self):
#         self.__label_uuid.setEnabled(False)
#         self.__label_source.setEnabled(False)
#         self.setWindowTitle('笔记')
#         self.__datetime_time.setCalendarPopup(True)
#
#         self.__button_apply.clicked.connect(self.on_button_apply)
#         self.__button_cancel.clicked.connect(self.on_button_cancel)
#
#     def on_button_apply(self):
#         if self.__current_record is None:
#             self.__current_record = HistoricalRecord()
#         else:
#             self.__current_record.reset()
#
#         if not self.ui_to_record(self.__current_record):
#             QMessageBox.information(self,
#                                     QtCore.QCoreApplication.translate('History', '错误'),
#                                     QtCore.QCoreApplication.translate('History', '采集界面数据错误'),
#                                     QMessageBox.Ok, QMessageBox.Ok)
#             return
#         if self.__source is None or self.__source == '':
#             QMessageBox.information(self,
#                                     QtCore.QCoreApplication.translate('History', '错误'),
#                                     QtCore.QCoreApplication.translate('History', '没有指定数据源，无法保存'),
#                                     QMessageBox.Ok, QMessageBox.Ok)
#             return
#
#         self.__current_record.set_source(self.__source)
#         self.__history.update_records([self.__current_record])
#
#         records = self.__history.get_record_by_source(self.__source)
#         result = HistoricalRecordLoader.to_local_source(records, self.__source)
#
#         if not result:
#             QMessageBox.information(self,
#                                     QtCore.QCoreApplication.translate('History', '错误'),
#                                     QtCore.QCoreApplication.translate('History', '保存到数据源 [%s] 失败' % self.__source),
#                                     QMessageBox.Ok, QMessageBox.Ok)
#             return
#
#         self.close()
#
#     def on_button_cancel(self):
#         self.close()
#
#     # ---------------------------------------------------------------------------
#
#     def set_memo(self, memo: HistoricalRecord):
#         self.__current_record = memo
#         self.__source = memo.source()
#         self.record_to_ui(memo)
#
#     def set_source(self, source: str):
#         self.__source = source
#
#     def set_memo_datetime(self, date_time: datetime.datetime):
#         self.__datetime_time.setDateTime(date_time)
#
#     # -------------------------------- Operation --------------------------------
#
#     def clear_ui(self):
#         self.__label_uuid.setText('')
#         self.__label_source.setText('')
#         self.__text_record.clear()
#
#     def ui_to_record(self, record: HistoricalRecord) -> bool:
#         input_time = self.__datetime_time.dateTime()
#         input_memo = self.__text_record.toPlainText()
#         date_time = input_time.toPyDateTime()
#
#         record.set_label_tags('time', date_time.strftime('%Y-%m-%d %H:%M:%S'))
#         record.set_label_tags('event', input_memo)
#         record.set_focus_label('time')
#         return True
#
#     def record_to_ui(self, record: HistoricalRecord or str):
#         self.clear_ui()
#
#         self.__label_uuid.setText(LabelTagParser.tags_to_text(record.uuid()))
#         self.__label_source.setText(self.__source)
#         self.__text_record.setText(LabelTagParser.tags_to_text(record.event()))
#
#         since = record.since()
#         pytime = HistoryTime.tick_to_pytime(since)
#         self.__datetime_time.setDateTime(pytime)


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

        # vnpy chart
        self.__vnpy_chart = ChartWidget()

        # Timer for update stock list
        self.__timer = QTimer()
        self.__timer.setInterval(1000)
        self.__timer.timeout.connect(self.on_timer)
        self.__timer.start()

        # Ui component
        self.__combo_name = QComboBox()
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

        # ------------------ Right Button Menu ------------------

        # self.__time_axis.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.__time_axis.customContextMenuRequested.connect(self.on_custom_menu)

        self.__vnpy_chart.add_plot("candle", hide_x_axis=True)
        self.__vnpy_chart.add_plot("memo", maximum_height=50)
        self.__vnpy_chart.add_plot("volume", maximum_height=200)

        self.__vnpy_chart.add_item(CandleItem, "candle", "candle")
        self.__vnpy_chart.add_item(MemoItem, "memo", "memo")
        self.__vnpy_chart.add_item(VolumeItem, "volume", "volume")

        self.__vnpy_chart.add_cursor()

        self.__vnpy_chart.scene().sigMouseClicked.connect(self.on_chart_clicked)

    def on_chart_clicked(self, event):
        items = self.__vnpy_chart.scene().items(event.scenePos())
        print(str(items))
        # print("Plots:" + str([x for x in items if isinstance(x, pg.PlotItem)]))

    def on_timer(self):
        # Check stock list ready and update combobox
        data_utility = self.__sas.get_data_hub_entry().get_data_utility()
        if data_utility.stock_cache_ready():
            stock_list = data_utility.get_stock_list()
            for stock_identity, stock_name in stock_list:
                self.__combo_name.addItem(stock_identity + ' | ' + stock_name, stock_identity)
            self.__timer.stop()

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

        if not self.load_for_securities(input_securities, adjust_method, return_style):
            QMessageBox.information(self,
                                    QtCore.QCoreApplication.translate('History', '没有数据'),
                                    QtCore.QCoreApplication.translate('History', '没有交易数据，请检查证券编码或更新本地数据'),
                                    QMessageBox.Ok, QMessageBox.Ok)

    # ------------------------------ Right Click Menu ------------------------------

    def on_custom_menu(self, pos: QPoint):
        pass
        # align = self.__time_axis.align_from_point(pos)
        # thread = self.__time_axis.thread_from_point(pos)
        #
        # opt_add_memo = None
        #
        # menu = QMenu()
        # if thread == self.__thread_memo:
        #     opt_add_memo = menu.addAction("新增笔记")
        #     action = menu.exec_(self.__time_axis.mapToGlobal(pos))
        #
        #     if action == opt_add_memo:
        #         tick = self.__time_axis.tick_from_point(pos)
        #         date_time = HistoryTime.tick_to_pytime(tick)
        #         editor = StockMemoEditor(self.__history)
        #         editor.set_memo_datetime(date_time)
        #         editor.set_source(self.__memo_file)
        #         editor.exec_()

    # --------------------------------------------------------------

    # def popup_editor_for_index(self, index: HistoricalRecord):
    #     if index is None:
    #         print('None index.')
    #         return
    #     editor = StockMemoEditor(self.__history)
    #     editor.set_memo(index)
    #     editor.exec_()

    # ------------------------------------------------------------------------------

    def load_for_securities(self, securities: str, adjust_method: int, return_style: int) -> bool:
        data_utility = self.__sas.get_data_hub_entry().get_data_utility()
        index_dict = data_utility.get_support_index()

        if securities != self.__paint_securities or self.__paint_trade_data is None:
            if securities in index_dict.keys():
                uri = 'TradeData.Index.Daily'
            else:
                uri = 'TradeData.Stock.Daily'
            trade_data = self.__sas.get_data_hub_entry().get_data_center().query(uri, securities)

            # base_path = path.dirname(path.abspath(__file__))
            # history_path = path.join(base_path, 'History')
            # depot_path = path.join(history_path, 'depot')
            # his_file = path.join(depot_path, securities + '.his')

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

        # n = 1000
        # history = bars[:n]
        # new_data = bars[n:]

        # def update_bar():
        #     bar = new_data.pop(0)
        #     widget.update_bar(bar)

        # timer = QtCore.QTimer()
        # timer.timeout.connect(update_bar)
        # timer.start(100)

        self.__vnpy_chart.update_history(bars)

        bar_manager = self.__vnpy_chart.get_bar_manager()
        bar_manager.set_item_data(datetime.datetime(2020, 1, 2, 0, 0, 0), 'memo', ['memo'] * 2)
        bar_manager.set_item_data(datetime.datetime(2020, 1, 9, 0, 0, 0), 'memo', ['memo'] * 1)
        bar_manager.set_item_data(datetime.datetime(2020, 1, 16, 0, 0, 0), 'memo', ['memo'] * 8)
        bar_manager.set_item_data(datetime.datetime(2020, 1, 23, 0, 0, 0), 'memo', ['memo'] * 9)
        bar_manager.set_item_data(datetime.datetime(2020, 1, 31, 0, 0, 0), 'memo', ['memo'] * 13)
        bar_manager.set_item_data_range('memo', 0.0, 13.0)

        memo_item = self.__vnpy_chart.get_item('memo')
        if memo_item is not None:
            memo_item.update_history(None)

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
    # app = QApplication(sys.argv)
    # StockMemoEditor(History()).exec()
    pass


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




















