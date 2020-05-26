import datetime
import sys
import traceback
from os import path
import pandas as pd
from PyQt5 import QtWidgets, QtCore

from StockAnalysisSystem.porting.vnpy_chart import *


# ----------------------------------------------------------------------------------------------------------------------

def main():
    app = QtWidgets.QApplication([])

    root_path = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
    df = pd.read_csv(path.join(root_path, 'TestData', '000001.SSE.CSV'))

    bars = []
    for index, row in df.iterrows():

        date_time = datetime.datetime.strptime(row['trade_date'], '%Y-%m-%d')
        bar_data = BarData(datetime=date_time,
                           exchange=Exchange.SSE,
                           symbol='000001',
                           gateway_name='ABC')

        bar_data.interval = Interval.DAILY
        bar_data.volume = row['amount'] * 10000
        bar_data.open_interest = row['open']
        bar_data.open_price = row['open']
        bar_data.high_price = row['high']
        bar_data.low_price = row['low']
        bar_data.close_price = row['close']
        bars.append(bar_data)

    widget = ChartWidget()
    widget.add_plot("candle", hide_x_axis=True)
    widget.add_plot("volume", maximum_height=200)
    widget.add_item(CandleItem, "candle", "candle")
    widget.add_item(VolumeItem, "volume", "volume")
    widget.add_cursor()

    n = 1000
    history = bars[:n]
    new_data = bars[n:]

    widget.update_history(history)

    def update_bar():
        bar = new_data.pop(0)
        widget.update_bar(bar)

    timer = QtCore.QTimer()
    timer.timeout.connect(update_bar)
    # timer.start(100)

    widget.show()
    app.exec_()


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


