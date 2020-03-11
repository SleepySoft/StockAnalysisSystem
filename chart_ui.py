
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
import mplfinance as mpf
from matplotlib.dates import DateFormatter, WeekdayLocator,DayLocator, MONDAY

from PyQt5.QtCore import pyqtSignal, QProcess
from PyQt5.QtWidgets import QGridLayout, QLineEdit, QFileDialog, QComboBox

from Utiltity.ui_utility import *
from DataHub.DataHubEntry import *

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

        df['trade_date'] = df['trade_date'].apply(lambda d: mdates.date2num(d.to_pydatetime()))
        adjust_ratio = df['adj_factor']

        price_open = df['open'] * adjust_ratio
        price_close = df['close'] * adjust_ratio
        price_high = df['high'] * adjust_ratio
        price_low = df['low'] * adjust_ratio

        self.__figure.clear()
        ax = self.__figure.add_subplot(111)

        mpf.(ax, price_open, price_close, price_high, price_low,
                              width=0.5,
                              colorup='r', colordown='g')

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






































