import os

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QTimer, QDateTime, QPoint, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QButtonGroup, QDateTimeEdit, QApplication, QLabel, QTextEdit, QPushButton, QVBoxLayout, \
    QMessageBox, QWidget, QComboBox, QCheckBox, QRadioButton, QLineEdit, QAbstractItemView, QFileDialog, QDialog
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent

from StockAnalysisSystem.porting.vnpy_chart import *
from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.ui_utility import *
from StockAnalysisSystem.core.Utiltity.securities_selector import SecuritiesSelector

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.append(root_path)

from StockMemo.MemoUtility import *
from StockMemo.StockMemoEditor import StockMemoEditor


# ----------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------- class StockChartUi -------------------------------------------------
# --------------------------------------------  The Candle Stick Interface ---------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

class StockChartUi(QWidget):
    ADJUST_TAIL = 0
    ADJUST_HEAD = 1
    ADJUST_NONE = 2

    RETURN_LOG = 3
    RETURN_SIMPLE = 4

    def __init__(self, memo_data: StockMemoData):
        self.__memo_data = memo_data
        super(StockChartUi, self).__init__()

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
            adjust_method = StockChartUi.ADJUST_TAIL
        elif self.__radio_adj_head.isChecked():
            adjust_method = StockChartUi.ADJUST_HEAD
        elif self.__radio_adj_none.isChecked():
            adjust_method = StockChartUi.ADJUST_NONE
        else:
            adjust_method = StockChartUi.ADJUST_NONE

        if self.__radio_log_return.isChecked():
            return_style = StockChartUi.RETURN_LOG
        elif self.__radio_simple_return.isChecked():
            return_style = StockChartUi.RETURN_SIMPLE
        else:
            return_style = StockChartUi.RETURN_SIMPLE

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
        if adjust_method == StockChartUi.ADJUST_TAIL and 'adj_factor' in self.__paint_trade_data.columns:
            trade_data['open'] = self.__paint_trade_data['open'] * self.__paint_trade_data['adj_factor']
            trade_data['close'] = self.__paint_trade_data['close'] * self.__paint_trade_data['adj_factor']
            trade_data['high'] = self.__paint_trade_data['high'] * self.__paint_trade_data['adj_factor']
            trade_data['low'] = self.__paint_trade_data['low'] * self.__paint_trade_data['adj_factor']
        elif adjust_method == StockChartUi.ADJUST_HEAD and 'adj_factor' in self.__paint_trade_data.columns:
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

        if return_style == StockChartUi.RETURN_LOG:
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








