
#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2017/08/08
@file: DataTable.py
@function:
@modify:
"""
import traceback
from os import sys, path, system

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.dates as mdates
import mpl_finance as mpf
from matplotlib.dates import DateFormatter, WeekdayLocator,DayLocator, MONDAY

from PyQt5.QtCore import pyqtSignal, QProcess
from PyQt5.QtWidgets import QGridLayout, QLineEdit, QFileDialog, QComboBox

from Utiltity.ui_utility import *
from DataHub.DataHubEntry import *
from Utiltity.time_utility import *

pyplot_logger = logging.getLogger('matplotlib')
pyplot_logger.setLevel(level=logging.INFO)


# https://stackoverflow.com/questions/12459811/how-to-embed-matplotlib-in-pyqt-for-dummies

class ChartUi(QWidget):
    def __init__(self, datahub_entry: DataHubEntry):
        super(ChartUi, self).__init__()

        # ---------------- ext var ----------------

        self.__data_entry = datahub_entry
        self.__data_center = self.__data_entry.get_data_center() if self.__data_entry is not None else None
        self.__data_utility = self.__data_entry.get_data_utility() if self.__data_entry is not None else None

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
        self.plot_stock_price()

        # import random
        # data = [random.random() for i in range(10)]
        # self.__figure.clear()
        # ax = self.__figure.add_subplot(111)
        # ax.plot(data, '*-')
        # self.__canvas.draw()

    # https://stackoverflow.com/questions/42373104/since-matplotlib-finance-has-been-deprecated-how-can-i-use-the-new-mpl-finance

    def plot_stock_price(self):
        df = self.__data_center.query('TradeData.Stock.Daily', '600000.SSE')

        df = df[df['trade_date'] > years_ago(1)]

        # df['trade_date'] = df['trade_date'].apply(lambda d: mdates.date2num(d.to_pydatetime()))
        adjust_ratio = df['adj_factor']

        price_open = df['open'] * adjust_ratio
        price_close = df['close'] * adjust_ratio
        price_high = df['high'] * adjust_ratio
        price_low = df['low'] * adjust_ratio

        self.__figure.clear()
        ax1 = self.__figure.add_subplot(2, 1, 1)
        ax2 = self.__figure.add_subplot(2, 1, 2)

        time_serial = pd.to_datetime(df['trade_date'], format="%Y/%m/%d")

        # ax1 = plt.subplot2grid((3, 1), (0, 0), rowspan=2, colspan=1)  # 佔全圖2/3的子圖一
        ax1.set_xticks(range(0, len(time_serial), 10))  # 設定X軸座標
        ax1.set_xticklabels(time_serial)  # 設定X軸標籤
        mpf.candlestick2_ohlc(ax1, df['open'], df['high'], df['low'], df['close'], width=0.6, colorup='r',
                              colordown='k', alpha=1)  # 畫出K線圖
        ax1.tick_params('x', bottom=False, labelbottom=False)  # 子圖一不顯示X軸標籤
        ax1.set_axisbelow(True)  # 設定格線在最底圖層
        ax1.grid(True)  # 畫格線

        # ax2 = plt.subplot2grid((3, 1), (2, 0), rowspan=1, colspan=1, sharex=ax1)  # 佔全圖1/3的子圖二，設定X軸座標與子圖一相同
        mpf.volume_overlay(ax2, df['open'], df['close'], df['amount'] / 1000, colorup='b', colordown='b',
                           width=0.6, alpha=1)  # 畫出成交量
        ax2.set_axisbelow(True)  # 設定格線在最底圖層
        ax2.grid(True)  # 畫格線

        plt.gcf().autofmt_xdate()  # 斜放X軸標籤
        self.__canvas.draw()

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

        self.__canvas.draw()


# ----------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    dlg = WrapperQDialog(ChartUi(None))
    dlg.exec()


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






































