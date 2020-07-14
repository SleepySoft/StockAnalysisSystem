from abc import abstractmethod
from typing import List, Dict, Tuple

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

from .data import BarData
from .base import UP_COLOR, DOWN_COLOR, MEMO_COLOR, PEN_WIDTH, BAR_WIDTH
from .manager import BarManager


class ChartItem(pg.GraphicsObject):
    """"""

    def __init__(self, manager: BarManager):
        """"""
        super().__init__()

        self._manager: BarManager = manager

        self._bar_pictures: Dict[int, QtGui.QPicture] = {}
        self._item_picture: QtGui.QPicture = None

        self._up_pen: QtGui.QPen = pg.mkPen(
            color=UP_COLOR, width=PEN_WIDTH
        )
        self._up_brush: QtGui.QBrush = pg.mkBrush(color=UP_COLOR)

        self._down_pen: QtGui.QPen = pg.mkPen(
            color=DOWN_COLOR, width=PEN_WIDTH
        )
        self._down_brush: QtGui.QBrush = pg.mkBrush(color=DOWN_COLOR)

        self._rect_area: Tuple[float, float] = None

        # Very important! Only redraw the visible part and improve speed a lot.
        self.setFlag(self.ItemUsesExtendedStyleOption)

    @abstractmethod
    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """
        Draw picture for specific bar.
        """
        pass

    @abstractmethod
    def boundingRect(self) -> QtCore.QRectF:
        """
        Get bounding rectangles for item.
        """
        pass

    @abstractmethod
    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        Get range of y-axis with given x-axis range.

        If min_ix and max_ix not specified, then return range with whole data set.
        """
        pass

    @abstractmethod
    def get_info_text(self, ix: int) -> str:
        """
        Get information text to show by cursor.
        """

    def set_visible(self, visible: bool):
        pass

    def refresh_history(self):
        self._bar_pictures.clear()

        bars = self._manager.get_all_bars()
        for ix, bar in enumerate(bars):
            bar_picture = self._draw_bar_picture(ix, bar)
            self._bar_pictures[ix] = bar_picture

        self.update()

    def update_history(self, history: List[BarData]) -> BarData:
        """
        Update a list of bar data.
        """
        self.refresh_history()

    def update_bar(self, bar: BarData) -> BarData:
        """
        Update single bar data.
        """
        ix = self._manager.get_index(bar.datetime)

        bar_picture = self._draw_bar_picture(ix, bar)
        self._bar_pictures[ix] = bar_picture

        self.update()

    def update(self) -> None:
        """
        Refresh the item.
        """
        if self.scene():
            self.scene().update()

    def paint(
        self,
        painter: QtGui.QPainter,
        opt: QtWidgets.QStyleOptionGraphicsItem,
        w: QtWidgets.QWidget
    ):
        """
        Reimplement the paint method of parent class.

        This function is called by external QGraphicsView.
        """
        rect = opt.exposedRect

        min_ix = int(rect.left())
        max_ix = int(rect.right())
        max_ix = min(max_ix, len(self._bar_pictures))

        rect_area = (min_ix, max_ix)
        if rect_area != self._rect_area or not self._item_picture:
            self._rect_area = rect_area
            self._draw_item_picture(min_ix, max_ix)

        self._item_picture.play(painter)

    def _draw_item_picture(self, min_ix: int, max_ix: int) -> None:
        """
        Draw the picture of item in specific range.
        """
        self._item_picture = QtGui.QPicture()
        painter = QtGui.QPainter(self._item_picture)

        for n in range(min_ix, max_ix):
            bar_picture = self._bar_pictures[n]
            if bar_picture is not None:
                bar_picture.play(painter)

        painter.end()

    def clear_all(self) -> None:
        """
        Clear all data in the item.
        """
        self._item_picture = None
        self._bar_pictures.clear()
        self.update()


class CandleItem(ChartItem):
    """"""

    def __init__(self, manager: BarManager):
        """"""
        self._y_dynamic = True
        super().__init__(manager)

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """"""
        # Create objects
        candle_picture = QtGui.QPicture()
        painter = QtGui.QPainter(candle_picture)

        if bar.high_price >= 0.01:
            # Set painter color
            if bar.close_price >= bar.open_price:
                painter.setPen(self._up_pen)
                painter.setBrush(self._up_brush)
            else:
                painter.setPen(self._down_pen)
                painter.setBrush(self._down_brush)

            # Draw candle shadow
            painter.drawLine(
                QtCore.QPointF(ix, bar.high_price),
                QtCore.QPointF(ix, bar.low_price)
            )

            # Draw candle body
            if bar.open_price == bar.close_price:
                painter.drawLine(
                    QtCore.QPointF(ix - BAR_WIDTH, bar.open_price),
                    QtCore.QPointF(ix + BAR_WIDTH, bar.open_price),
                )
            else:
                rect = QtCore.QRectF(
                    ix - BAR_WIDTH,
                    bar.open_price,
                    BAR_WIDTH * 2,
                    bar.close_price - bar.open_price
                )
                painter.drawRect(rect)

        # Finish
        painter.end()
        return candle_picture
        # return None

    def boundingRect(self) -> QtCore.QRectF:
        """"""
        min_price, max_price = self._manager.get_price_range()
        rect = QtCore.QRectF(
            0,
            min_price,
            len(self._bar_pictures),
            max_price - min_price
        )
        return rect

    def set_y_range_dynamic(self, dynamic: bool):
        self._y_dynamic = dynamic

    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        Get range of y-axis with given x-axis range.

        If min_ix and max_ix not specified, then return range with whole data set.
        """
        if self._y_dynamic:
            min_price, max_price = self._manager.get_price_range(min_ix, max_ix)
        else:
            min_price, max_price = self._manager.get_price_range()
        return min_price, max_price

    def get_info_text(self, ix: int) -> str:
        """
        Get information text to show by cursor.
        """
        bar = self._manager.get_bar(ix)

        if bar:
            words = [
                "Date",
                bar.datetime.strftime("%Y-%m-%d"),
                "",
                "Time",
                bar.datetime.strftime("%H:%M"),
                "",
                "Open",
                ('%.2f' % bar.open_price),
                "",
                "High",
                ('%.2f' % bar.high_price),
                "",
                "Low",
                ('%.2f' % bar.low_price),
                "",
                "Close",
                ('%.2f' % bar.close_price),
            ]
            text = "\n".join(words)
        else:
            text = ""

        return text


class VolumeItem(ChartItem):
    """"""

    def __init__(self, manager: BarManager):
        """"""
        super().__init__(manager)

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """"""
        # Create objects
        volume_picture = QtGui.QPicture()
        painter = QtGui.QPainter(volume_picture)

        # Set painter color
        if bar.close_price >= bar.open_price:
            painter.setPen(self._up_pen)
            painter.setBrush(self._up_brush)
        else:
            painter.setPen(self._down_pen)
            painter.setBrush(self._down_brush)

        # Draw volume body
        rect = QtCore.QRectF(
            ix - BAR_WIDTH,
            0,
            BAR_WIDTH * 2,
            bar.volume
        )
        painter.drawRect(rect)

        # Finish
        painter.end()
        return volume_picture

    def boundingRect(self) -> QtCore.QRectF:
        """"""
        min_volume, max_volume = self._manager.get_volume_range()
        rect = QtCore.QRectF(
            0,
            min_volume,
            len(self._bar_pictures),
            max_volume - min_volume
        )
        return rect

    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        Get range of y-axis with given x-axis range.

        If min_ix and max_ix not specified, then return range with whole data set.
        """
        min_volume, max_volume = self._manager.get_volume_range(min_ix, max_ix)
        return min_volume, max_volume

    def get_info_text(self, ix: int) -> str:
        """
        Get information text to show by cursor.
        """
        bar = self._manager.get_bar(ix)

        if bar:
            text = f"Volume {bar.volume}"
        else:
            text = ""

        return text


class MemoItem(ChartItem):
    """"""
    def __init__(self, manager: BarManager):
        """"""
        self._border_pen: QtGui.QPen = pg.mkPen(
            color=MEMO_COLOR, width=PEN_WIDTH
        )
        self._background_brush: QtGui.QBrush = pg.mkBrush(color=UP_COLOR)
        super().__init__(manager)

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture or None:
        """"""
        memo = self._manager.get_item_data(ix, 'memo')
        if memo is None:
            return None

        # Create objects
        memo_picture = QtGui.QPicture()
        painter = QtGui.QPainter(memo_picture)

        painter.setPen(self._border_pen)
        painter.setBrush(self._background_brush)

        rect = QtCore.QRectF(
            ix - BAR_WIDTH + 0.1,
            0,
            BAR_WIDTH * 2 - 0.1,
            len(memo)
        )
        painter.drawRect(rect)

        # Finish
        painter.end()
        return memo_picture

    def boundingRect(self) -> QtCore.QRectF:
        """"""
        min_data, max_data = self._manager.get_item_data_range('memo', (0, 10))
        rect = QtCore.QRectF(
            0,
            min_data,
            len(self._bar_pictures),
            max_data
        )
        return rect

    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        return self._manager.get_item_data_range('memo', (0, 10))

    def get_info_text(self, ix: int) -> str:
        """
        Get information text to show by cursor.
        """
        memo = self._manager.get_item_data(ix, 'memo')
        if memo is not None:
            text = "Memo: %s" % len(memo)
        else:
            text = "Memo: 0"
        return text

