import logging
from os import sys, path
from PyQt5.QtCore import pyqtSignal, QProcess
from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QLineEdit, QFileDialog, QComboBox, QVBoxLayout

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Analyzer.AnalyzerUtility import *
    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
    from stock_analysis_system import StockAnalysisSystem
except Exception as e:
    sys.path.append(root_path)

    from Analyzer.AnalyzerUtility import *
    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
    from stock_analysis_system import StockAnalysisSystem
finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------


pyplot_logger = logging.getLogger('matplotlib')
pyplot_logger.setLevel(level=logging.INFO)


# https://stackoverflow.com/questions/12459811/how-to-embed-matplotlib-in-pyqt-for-dummies
# https://stackoverflow.com/questions/42373104/since-matplotlib-finance-has-been-deprecated-how-can-i-use-the-new-mpl-finance

class ChartLab(QWidget):
    def __init__(self, datahub_entry: DataHubEntry):
        super(ChartLab, self).__init__()

        # ---------------- ext var ----------------

        self.__data_hub = datahub_entry
        self.__data_center = self.__data_hub.get_data_center() if self.__data_hub is not None else None
        self.__data_utility = self.__data_hub.get_data_utility() if self.__data_hub is not None else None

        # ------------- plot resource -------------

        self.__figure = plt.figure()
        self.__canvas = FigureCanvas(self.__figure)

        # -------------- ui resource --------------

        self.__button_draw = QPushButton('Draw')

        self.init_ui()

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.setMinimumSize(600, 400)

        main_layout.addWidget(self.__canvas)
        main_layout.addWidget(self.__button_draw)

    def __config_control(self):
        self.__button_draw.clicked.connect(self.on_button_draw)

    def on_button_draw(self):
        self.plot()

    def plot(self):
        self.plot_histogram_statistics()

    def plot_histogram_statistics(self):
        fields_balance_sheet = ['货币资金', '资产总计', '负债合计',
                                '短期借款', '一年内到期的非流动负债', '其他流动负债',
                                '长期借款', '应付债券', '其他非流动负债',
                                '应收票据', '其他流动负债', '流动负债合计',
                                '交易性金融资产', '可供出售金融资产']
        df, result = query_readable_annual_report_pattern(
            self.__data_hub, 'Finance.BalanceSheet', '',
            (text_auto_time('2019-12-01'), text_auto_time('2019-12-31')),
            fields_balance_sheet)
        if result is not None:
            print('Data Error')

        df['净资产'] = df['资产总计'] - df['负债合计']
        df['短期负债'] = df['短期借款'] + df['一年内到期的非流动负债'] + df['其他流动负债']
        df['有息负债'] = df['短期负债'] + df['长期借款'] + df['应付债券'] + df['其他非流动负债']
        df['金融资产'] = df['交易性金融资产'] + df['可供出售金融资产']

        df_calc = pd.DataFrame()
        df_calc['period'] = df['period']
        df_calc['stock_identity'] = df['stock_identity']
        df_calc['货币资金/有息负债'] = df['货币资金'] / df['有息负债']

        ranges = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        df_calc.groupby(pd.cut(df.a, ranges)).count()

        print(df_calc)


    # def plot_stock_price(self):
        # df = self.__data_center.query('TradeData.Stock.Daily', '600000.SSE')
        #
        # df = df[df['trade_date'] > years_ago(1)]
        #
        # # df['trade_date'] = df['trade_date'].apply(lambda d: mdates.date2num(d.to_pydatetime()))
        # adjust_ratio = df['adj_factor']
        #
        # price_open = df['open'] * adjust_ratio
        # price_close = df['close'] * adjust_ratio
        # price_high = df['high'] * adjust_ratio
        # price_low = df['low'] * adjust_ratio
        #
        # self.__figure.clear()
        # ax1 = self.__figure.add_subplot(2, 1, 1)
        # ax2 = self.__figure.add_subplot(2, 1, 2)
        #
        # time_serial = pd.to_datetime(df['trade_date'], format="%Y/%m/%d")
        #
        # # ax1 = plt.subplot2grid((3, 1), (0, 0), rowspan=2, colspan=1)  # 佔全圖2/3的子圖一
        # ax1.set_xticks(range(0, len(time_serial), 10))  # 設定X軸座標
        # ax1.set_xticklabels(time_serial)  # 設定X軸標籤
        # mpf.candlestick2_ohlc(ax1, df['open'], df['high'], df['low'], df['close'], width=0.6, colorup='r',
        #                       colordown='k', alpha=1)  # 畫出K線圖
        # ax1.tick_params('x', bottom=False, labelbottom=False)  # 子圖一不顯示X軸標籤
        # ax1.set_axisbelow(True)  # 設定格線在最底圖層
        # ax1.grid(True)  # 畫格線
        #
        # # ax2 = plt.subplot2grid((3, 1), (2, 0), rowspan=1, colspan=1, sharex=ax1)  # 佔全圖1/3的子圖二，設定X軸座標與子圖一相同
        # mpf.volume_overlay(ax2, df['open'], df['close'], df['amount'] / 1000, colorup='b', colordown='b',
        #                    width=0.6, alpha=1)  # 畫出成交量
        # ax2.set_axisbelow(True)  # 設定格線在最底圖層
        # ax2.grid(True)  # 畫格線
        #
        # plt.gcf().autofmt_xdate()  # 斜放X軸標籤
        # self.__canvas.draw()

        # mpf.candlestick2_ochl(axes, price_open, price_close, price_high, price_low, colorup='r', colordown='g')
        #
        # axes.set_xlabel('日期')
        # axes.set_ylabel('价格')
        # axes.set_xlim(0, len(df['trade_date']))
        # axes.set_xticks(range(0, len(df['trade_date']), 15))
        #
        # time_serial = pd.to_datetime(df['trade_date'], format="%Y/%m/%d")
        # axes.set_xticklabels([time_serial[x] for x in axes.get_xticks()])  # 标签设置为日期
        #
        # # X-轴每个ticker标签都向右倾斜45度
        # for label in axes.xaxis.get_ticklabels():
        #     label.set_rotation(45)
        #     label.set_fontsize(10)  # 设置标签字体
        # plt.show()

        # self.__canvas.draw()


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': '29ae0dea-fbb6-490e-b1c8-f5dd206bf661',
        'plugin_name': 'ChartLab',
        'plugin_version': '0.0.0.1',
        'tags': ['Chart', 'Test', 'Sleepy'],
    }


def plugin_adapt(method: str) -> bool:
    return method in ['widget']


def plugin_capacities() -> list:
    return ['widget']
    # return [
    #     'period',
    #     'thread',
    #     'widget',
    # ]


# ----------------------------------------------------------------------------------------------------------------------

sasEntry = None


def init(sas: StockAnalysisSystem) -> bool:
    try:
        global sasEntry
        sasEntry = sas
    except Exception as e:
        pass
    finally:
        pass
    return True


def widget(parent: QWidget) -> (QWidget, dict):
    return ChartLab(sasEntry.get_data_hub_entry()), {'name': 'ChartLab', 'show': False}


















