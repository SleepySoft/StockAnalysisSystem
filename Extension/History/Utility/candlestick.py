import copy
import time
import random
import numpy as np
import pandas as pd
import traceback, math
from PyQt5.QtCore import QRect, QPoint, QSize
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QPolygon, QFontMetrics

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))


try:
    from viewer_ex import *
    from Utility.history_time import *
    from Utility.viewer_utility import *
except Exception as e:
    sys.path.append(root_path)

    from viewer_ex import *
    from Utility.history_time import *
    from Utility.viewer_utility import *
finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------
#                                                  class Candlestick
# ----------------------------------------------------------------------------------------------------------------------

class Candlestick(AxisItem):
    COLOR_INCREASE = QColor(255, 0, 0)
    COLOR_DECREASE = QColor(0, 255, 0)

    def __init__(self, lower_limit: float, upper_limit: float,
                 date: HistoryTime.TICK, _open: float, close: float, high: float, low: float):
        super(Candlestick, self).__init__(None, {})
        self.__lower_limit = min(lower_limit, upper_limit)
        self.__upper_limit = max(lower_limit, upper_limit)
        self.__date = date
        self.__open = _open
        self.__close = close
        self.__high = high
        self.__low = low

        metrics = self.get_item_metrics()
        metrics.set_scale_range(date, date + HistoryTime.TICK_DAY - 1)

    def get_tip_text(self, on_tick: float) -> str:
        return 'Open %0.2f; Close: %0.2f; High: %0.2f; Close: %0.2f' % \
               (self.__open, self.__close, self.__high, self.__low)

    def arrange_item(self, outer_metrics: AxisMetrics):
        super(Candlestick, self).arrange_item(outer_metrics)

        since, until = self.__date, self.__date + HistoryTime.TICK_DAY - 1
        since_pixel = outer_metrics.value_to_pixel(since)
        until_pixel = outer_metrics.value_to_pixel(until)
        outer_since, outer_until = outer_metrics.get_longitudinal_range()
        self.item_metrics.set_scale_range(since, until)
        self.item_metrics.set_longitudinal_range(max(since_pixel, outer_since), min(until_pixel, outer_until))

    def paint(self, qp: QPainter):
        if self.get_outer_metrics().get_layout() == LAYOUT_HORIZON:
            self.__paint_horizon(qp)
        elif self.get_outer_metrics().get_layout() == LAYOUT_VERTICAL:
            self.__paint_vertical(qp)

    def __paint_horizon(self, qp: QPainter):
        metrics = self.get_item_metrics()
        item_rect = metrics.rect()

        value_y_mapping = AxisMapping(self.__lower_limit, self.__upper_limit, item_rect.bottom(), item_rect.top())
        # limit_range = self.__upper_limit - self.__lower_limit

        open_y = value_y_mapping.a_to_b(self.__open)
        close_y = value_y_mapping.a_to_b(self.__close)
        high_y = value_y_mapping.a_to_b(self.__high)
        low_y = value_y_mapping.a_to_b(self.__low)

        # open_y = item_rect.top() + item_rect.height() - item_rect.height() * (self.__open - self.__lower_limit) / limit_range
        # close_y = item_rect.top() + item_rect.height() - item_rect.height() * (self.__close - self.__lower_limit) / limit_range
        # high_y = item_rect.top() + item_rect.height() - item_rect.height() * (self.__high - self.__lower_limit) / limit_range
        # low_y = item_rect.top() + item_rect.height() - item_rect.height() * (self.__low - self.__lower_limit) / limit_range

        item_rect.setTop(open_y)
        item_rect.setBottom(close_y)

        mid_x = item_rect.center().x()
        color = Candlestick.COLOR_INCREASE if self.__close > self.__open else Candlestick.COLOR_DECREASE

        qp.setPen(color)
        qp.setBrush(color)
        qp.drawLine(mid_x, high_y, mid_x, low_y)
        qp.drawRect(item_rect)

    def __paint_vertical(self, qp: QPainter):
        pass


def build_candle_stick(df: pd.DataFrame,
                       open_field: str = 'open', close_field: str = 'close',
                       high_field: str = 'high', low_field: str = 'low',
                       time_field: str = 'trade_date') -> [Candlestick]:
    # lower = np.nanmin(df[low_field])
    upper = np.nanmax(df[high_field])

    # lower = -(-lower // 1)
    upper = -(-upper // 1)

    if upper < 100:
        upper = round(upper + 5, -1)
    elif upper < 1000:
        upper = round(upper + 50, -2)
    else:
        upper = round(upper + 500, -3)

    candle_sticks = []
    for index, row in df.iterrows():
        time_data = row[time_field]
        time_tick = HistoryTime.time_str_to_tick(time_data)
        candle_stick = Candlestick(0, upper, time_tick,
                                   row[open_field], row[close_field],
                                   row[high_field], row[low_field])
        candle_sticks.append(candle_stick)
    return candle_sticks


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    app = QApplication(sys.argv)

    # Threads
    thread = TimeThreadBase()
    thread.set_thread_color(THREAD_BACKGROUND_COLORS[0])

    df = pd.read_csv(path.join(root_path, 'res', '000001.SSE.CSV'))
    candle_sticks = build_candle_stick(df)

    for candle_stick in candle_sticks:
        thread.add_axis_items(candle_stick)

    # # CandleSticks
    # date = HistoryTime.now_tick() - HistoryTime.TICK_YEAR
    # for i in range(100):
    #     date += HistoryTime.TICK_DAY
    #     cs = Candlestick(0, 5000, date,
    #                      random.randint(2000, 3000), random.randint(2000, 3000),
    #                      random.randint(2000, 3000), random.randint(2000, 3000))
    #     thread.add_axis_items(cs)

    # HistoryViewerDialog
    history_viewer = HistoryViewerDialog()
    history_viewer.get_time_axis().set_axis_layout(LAYOUT_HORIZON)
    history_viewer.get_time_axis().set_axis_scale_step(HistoryTime.TICK_DAY)
    history_viewer.get_time_axis().set_axis_scale_step_limit(HistoryTime.TICK_DAY, HistoryTime.TICK_YEAR)
    history_viewer.get_time_axis().set_time_range(2010 * HistoryTime.TICK_YEAR, 2020 * HistoryTime.TICK_YEAR)
    history_viewer.get_time_axis().set_axis_time_range_limit(HistoryTime.years_to_seconds(1990), HistoryTime.now_tick())
    history_viewer.get_time_axis().add_history_thread(thread, ALIGN_RIGHT)
    history_viewer.exec()


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






















