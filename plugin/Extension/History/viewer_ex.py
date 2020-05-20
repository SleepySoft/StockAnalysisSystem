import copy
import time
import random
import traceback, math

from PyQt5.QtCore import QRect, QPoint, QSize
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QPolygon, QFontMetrics

from .editor import *
from .Utility.ui_utility import *
from .Utility.viewer_utility import *
from .Utility.history_public import *


# ------------------------------------------------------- Clock --------------------------------------------------------

class Clock:
    def __init__(self, start_flag: bool = True):
        self.__start_time = time.time()
        self.__start_flag = start_flag
        self.__freeze_time = None

    def reset(self):
        self.__start_flag = True
        self.__freeze_time = None
        self.__start_time = time.time()

    def freeze(self):
        self.__freeze_time = time.time()

    def elapsed(self) -> float:
        if self.__freeze_time is None:
            base_time = time.time()
        else:
            base_time = self.__freeze_time
        return (base_time - self.__start_time) if self.__start_flag else 0

    def elapsed_s(self) -> int:
        return int(self.elapsed()) if self.__start_flag else 0

    def elapsed_ms(self) -> int:
        return int(self.elapsed() * 1000) if self.__start_flag else 0


# ------------------------------------------------------ AxisItem ------------------------------------------------------

class AxisItem:
    def __init__(self, index: HistoricalRecord, extra: dict):
        self.extra = extra
        self.index = index
        self.item_metrics = AxisMetrics()
        self.outer_metrics = AxisMetrics()
        if self.index is not None:
            self.item_metrics.set_scale_range(self.index.since(), self.index.until())

    # ---------------------------------------------------------

    def get_index(self) ->HistoricalRecord:
        return self.index

    def get_tip_text(self, on_tick: float) -> str:
        return ''

    def get_item_metrics(self) -> AxisMetrics:
        return self.item_metrics

    def get_outer_metrics(self) -> AxisMetrics:
        return self.outer_metrics

    # ---------------------------------------------------------

    def shift_item(self, longitudinal: int, transverse: int):
        self.item_metrics.offset(longitudinal, transverse)

    def arrange_item(self, outer_metrics: AxisMetrics):
        self.outer_metrics = outer_metrics
        self.item_metrics = copy.deepcopy(outer_metrics)

        if self.index is not None:
            since_pixel = outer_metrics.value_to_pixel(self.index.since())
            until_pixel = outer_metrics.value_to_pixel(self.index.until())
            outer_since, outer_until = outer_metrics.get_longitudinal_range()
            self.item_metrics.set_scale_range(self.index.since(), self.index.until())
            self.item_metrics.set_longitudinal_range(max(since_pixel, outer_since), min(until_pixel, outer_until))

    def paint(self, qp: QPainter):
        assert False


# --------------------------------------------------- TimeThreadBase ---------------------------------------------------

class TimeThreadBase:
    REFERENCE_TRACK_WIDTH = 50

    def __init__(self):
        self.__axis_items = []
        self.__paint_items = []
        self.__metrics = AxisMetrics()
        self.__paint_color = QColor(255, 255, 255)
        self.__min_track_width = TimeThreadBase.REFERENCE_TRACK_WIDTH

    def paint(self, qp: QPainter):
        qp.setBrush(self.get_thread_color())
        qp.drawRect(self.get_thread_metrics().rect())
        clock = Clock()
        for item in self.__paint_items:
            item.paint(qp)
        print('Paint %s items, timespends: %sms' % (len(self.__paint_items), clock.elapsed_ms()))

    def clear(self):
        self.__axis_items.clear()

    def refresh(self):
        self.__paint_items.clear()
        since, until = self.get_thread_metrics().get_scale_range()
        for item in self.__axis_items:
            item_since, item_until = item.get_item_metrics().get_scale_range()
            if (item_since <= until) and (item_until >= since):
                self.__paint_items.append(item)
        self.arrange_items()

    def arrange_items(self):
        for item in self.__paint_items:
            item.arrange_item(self.get_thread_metrics())

    def add_axis_items(self, items: AxisItem or [AxisItem]):
        if isinstance(items, AxisItem):
            self.__axis_items.append(items)
        else:
            self.__axis_items.extend(items)

    def axis_item_from_point(self, point: QPoint) -> AxisItem or None:
        if not self.get_thread_metrics().contains(point):
            return None
        for i in range(len(self.__axis_items) - 1, -1, -1):
            item = self.__axis_items[i]
            if item.get_item_metrics().contains(point):
                return item
        return None

    # ------------------------------------------ Sets ------------------------------------------

    def set_thread_color(self, color: QColor):
        self.__paint_color = color

    def set_thread_metrics(self, metrics: AxisMetrics):
        # Use copy instead of assignment.
        self.__metrics.copy(metrics)

    def set_thread_min_track_width(self, width: int):
        self.__min_track_width = width

    # ------------------------------------------ Gets ------------------------------------------

    def get_axis_items(self) -> [AxisItem]:
        return self.__axis_items

    def get_paint_items(self) -> [AxisItem]:
        return self.__paint_items

    def get_thread_color(self) -> QColor:
        return self.__paint_color

    def get_thread_metrics(self) -> AxisMetrics:
        return self.__metrics

    def get_thread_min_track_width(self) -> int:
        return self.__min_track_width


# ----------------------------------------------------------------------------------------------------------------------
#                                                  class HistoryIndexBar
# ----------------------------------------------------------------------------------------------------------------------


class HistoryIndexBar(AxisItem):
    EVENT_BAR_WIDTH_LIMIT = 50

    def __init__(self, index: HistoricalRecord, extra: dict = {}):
        super(HistoryIndexBar, self).__init__(index, extra)
        self.__event_bk = QColor(243, 244, 246)
        self.__story_bk = QColor(185, 227, 217)

    # -----------------------------------------------------------------------

    def get_tip_text(self, on_tick: float) -> str:
        index = self.get_index()
        if index is None:
            return ''

        since = index.since()
        until = index.until()
        abstract_tags = index.get_tags('abstract')
        tip_text = abstract_tags[0] if len(abstract_tags) > 0 else ''
        tip_text = tip_text.strip()

        if since == until:
            # If it's a single time event
            # Show Event Year
            tip_text += ' : [' + str(HistoryTime.seconds_to_date(since)[0]) + ']'
        else:
            # If it's a period event.
            since_year = HistoryTime.seconds_to_date(since)[0]
            current_year = HistoryTime.seconds_to_date(int(on_tick))[0]
            until_year = HistoryTime.seconds_to_date(until)[0]

            # Show Current Year / Total Year
            tip_text += '(' + str(current_year - since_year + 1)
            tip_text += '/' + str(until_year - since_year + 1) + ')'

            # Show Period
            tip_text += ' : [' + str(since_year) + ' - ' + str(until_year) + ']'
        return tip_text

    def paint(self, qp: QPainter):
        if self.get_outer_metrics().get_layout() == LAYOUT_HORIZON:
            self.__paint_horizon(qp)
        elif self.get_outer_metrics().get_layout() == LAYOUT_VERTICAL:
            self.__paint_vertical(qp)

    def arrange_item(self, outer_metrics: AxisMetrics):
        super(HistoryIndexBar, self).arrange_item(outer_metrics)

        if self.index.since() == self.index.until():
            outer_left, outer_right = outer_metrics.get_transverse_limit()
            diagonal = abs(outer_right - outer_left)
            diagonal = min(diagonal, HistoryIndexBar.EVENT_BAR_WIDTH_LIMIT)
            half_diagonal = diagonal / 2
            since_pixel, until_pixel = self.get_item_metrics().get_longitudinal_range()
            since_pixel -= abs(half_diagonal)
            until_pixel += abs(half_diagonal)
            outer_since, outer_until = outer_metrics.get_longitudinal_range()
            self.item_metrics.set_longitudinal_range(max(since_pixel, outer_since), min(until_pixel, outer_until))

    def __paint_horizon(self, qp: QPainter):
        metrics = self.get_item_metrics()
        if self.get_index().since() == self.get_index().until():
            HistoryIndexBar.paint_event_bar_horizon(qp, metrics.rect(), self.__event_bk, metrics.get_align())
            HistoryIndexBar.paint_index_text(qp, self.get_index(), metrics.rect(), event_font)
        else:
            HistoryIndexBar.paint_period_bar(qp, metrics.rect(), self.__story_bk)
            HistoryIndexBar.paint_index_text(qp, self.get_index(), metrics.rect(), period_font)

    def __paint_vertical(self, qp: QPainter):
        metrics = self.get_item_metrics()
        if self.get_index().since() == self.get_index().until():
            HistoryIndexBar.paint_event_bar_vertical(qp, metrics.rect(), self.__event_bk, metrics.get_align())
            HistoryIndexBar.paint_index_text(qp, self.get_index(), metrics.rect(), event_font)
        else:
            HistoryIndexBar.paint_period_bar(qp, metrics.rect(), self.__story_bk)
            HistoryIndexBar.paint_index_text(qp, self.get_index(), metrics.rect(), period_font)

    @staticmethod
    def paint_event_bar_horizon(qp: QPainter, index_rect: QRect, back_ground: QColor, align: int):
        if align == ALIGN_RIGHT:
            rect = index_rect
            rect.setBottom(rect.bottom() - 10)
            arrow_points = [QPoint(rect.center().x(), rect.bottom() + 10),
                            rect.bottomLeft(), rect.topLeft(),
                            rect.topRight(), rect.bottomRight()]
        else:
            rect = index_rect
            rect.setTop(rect.top() + 10)
            arrow_points = [QPoint(rect.center().x(), rect.top() - 10),
                            rect.topRight(), rect.bottomRight(),
                            rect.bottomLeft(), rect.topLeft()]

        qp.setBrush(back_ground)
        qp.drawPolygon(QPolygon(arrow_points))

    @staticmethod
    def paint_event_bar_vertical(qp: QPainter, index_rect: QRect, back_ground: QColor, align: int):
        if align == ALIGN_RIGHT:
            rect = index_rect
            rect.setLeft(rect.left() + 10)
            arrow_points = [QPoint(rect.left() - 10, rect.center().y()),
                            rect.topLeft(), rect.topRight(),
                            rect.bottomRight(), rect.bottomLeft()]
        else:
            rect = index_rect
            rect.setRight(rect.right() - 10)
            arrow_points = [QPoint(rect.right() + 10, rect.center().y()),
                            rect.bottomRight(), rect.bottomLeft(),
                            rect.topLeft(), rect.topRight()]

        qp.setBrush(back_ground)
        qp.drawPolygon(QPolygon(arrow_points))

        # diamond_points = [QPoint(left, v_mid), QPoint(h_mid, v_mid - half_diagonal),
        #                   QPoint(right, v_mid), QPoint(h_mid, v_mid + half_diagonal)]
        # qp.setBrush(self.__event_bk)
        # qp.drawPolygon(QPolygon(diamond_points))

    @staticmethod
    def paint_period_bar(qp: QPainter, index_rect: QRect, back_ground: QColor):
        qp.setBrush(back_ground)
        qp.drawRect(index_rect)

    @staticmethod
    def paint_index_text(qp: QPainter, index: HistoricalRecord, index_rect: QRect, font: QFont):
        # qp.save()
        # qp.translate(rect.center())
        # qp.rotate(-90)
        # text_rect = QRect(rect)
        # if text_rect.top() < 0:
        #     text_rect.setTop(0)
        qp.setPen(Qt.SolidLine)
        qp.setPen(QPen(Qt.black, 1))
        qp.setFont(font)

        abstract = index.abstract()
        qp.drawText(index_rect, Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextWordWrap, abstract)
        # qp.restore()


# ----------------------------------------------------------------------------------------------------------------------
#                                                 class HistoryIndexTrack
# ----------------------------------------------------------------------------------------------------------------------

class HistoryIndexTrack(TimeThreadBase):
    REFERENCE_TRACK_WIDTH = 50

    def __init__(self):
        super(HistoryIndexTrack, self).__init__()
        
        self.__event_indexes = []
        self.__index_bar_table = {}

        self.__thread_tracks = []
        self.__thread_track_count = 0
        self.__thread_track_width = 50

        self.__flag_build_track = True
        self.__flag_layout_track = True
        self.__flag_layout_items = True
        self.__flag_arrange_items = True

    # ------------------------------------------ Sets ------------------------------------------

    def set_thread_event_indexes(self, indexes: list):
        self.clear()
        self.__event_indexes = indexes
        self.__index_bar_table.clear()
        for index in self.__event_indexes:
            bar = HistoryIndexBar(index)
            self.add_axis_items(bar)
            self.__index_bar_table[index] = bar
        self.__flag_layout_items = True
        self.refresh()

    # ------------------------------------------ Gets ------------------------------------------

    def get_index_axis_item(self, index: HistoricalRecord) -> HistoryIndexBar:
        bar = self.__index_bar_table.get(index, None)
        if bar is None:
            bar = HistoryIndexBar(index)
            self.__index_bar_table[index] = bar
        return bar

    # ------------------------------------------- Operations -------------------------------------------

    # def paint(self, qp: QPainter):
    #     qp.setBrush(self.get_thread_color())
    #     qp.drawRect(self.get_thread_metrics().rect())
    #
    #     for item in self.get_paint_items():
    #         item.paint(qp)
    #     if self.get_thread_metrics().get_layout() == LAYOUT_HORIZON:
    #         self.__paint_horizon(qp)
    #     elif self.get_thread_metrics().get_layout() == LAYOUT_VERTICAL:
    #         self.__paint_vertical(qp)
    #     else:
    #         assert False

    def arrange_items(self):
        paint_items = self.get_paint_items()
        paint_items.sort(key=lambda item: item.get_index().until() - item.get_index().since(), reverse=True)

        # Adjust track count
        track_count = self.get_thread_metrics().wide() / self.get_thread_min_track_width()
        track_count = max(1, int(track_count + 0.5))
        self.__thread_track_width = self.get_thread_metrics().wide() / track_count

        if self.__thread_track_count != track_count:
            self.__thread_track_count = track_count
            self.__flag_build_track = True
            self.__flag_layout_items = True
        self.__flag_layout_track = True
        self.__flag_arrange_items = True

        self.__update_paint_parameters()

    # ------------------------------------------------------------------------------------------

    # def __pickup_paint_indexes(self):
    #     self.__paint_indexes.clear()
    #     since, until = self.get_thread_metrics().get_scale_range()
    #     for index in self.__event_indexes:
    #         if index.period_adapt(since, until):
    #             # Pick the paint indexes and sort by its period length
    #             self.__paint_indexes.append(index)
    #
    #     # Sort method 1: The earlier index has higher priority -> The start track would be full filled.
    #     # self.__paint_indexes = sorted(self.__paint_indexes, key=lambda x: x.since())
    #
    #     # Sort method2: The longer index has higher priority -> The bar layout should be more stable.
    #     self.__paint_indexes.sort(key=lambda item: item.until() - item.since(), reverse=True)

    def __update_paint_parameters(self):
        if self.__flag_build_track:
            self.__build_track()
            self.__flag_build_track = False
        if self.__flag_layout_track:
            self.__layout_track()
            self.__flag_layout_track = False
        if self.__flag_layout_items:
            self.__layout_track_items()
            self.__flag_layout_items = False
        if self.__flag_arrange_items:
            self.__arrange_track_items()
            self.__flag_arrange_items = False

    def __build_track(self):
        self.__thread_tracks.clear()
        for track_index in range(self.__thread_track_count):
            track = TrackContext()
            self.__thread_tracks.append(track)

    def __layout_track(self):
        for track_index in range(len(self.__thread_tracks)):
            track_metrics = copy.deepcopy(self.get_thread_metrics())
            transverse_left, transverse_right = self.get_thread_metrics().get_transverse_limit()

            # TODO: How to do it with the same interface
            if self.get_thread_metrics().get_layout() == LAYOUT_HORIZON:
                if self.get_thread_metrics().get_align() == ALIGN_RIGHT:
                    track_metrics.set_transverse_limit(transverse_left - track_index * self.__thread_track_width,
                                                       transverse_left - (track_index + 1) * self.__thread_track_width)
                else:
                    track_metrics.set_transverse_limit(transverse_right + (track_index + 1) * self.__thread_track_width,
                                                       transverse_right + track_index * self.__thread_track_width)
            else:
                if self.get_thread_metrics().get_align() == ALIGN_RIGHT:
                    track_metrics.set_transverse_limit(transverse_left + track_index * self.__thread_track_width,
                                                       transverse_left + (track_index + 1) * self.__thread_track_width)
                else:
                    track_metrics.set_transverse_limit(transverse_right - (track_index + 1) * self.__thread_track_width,
                                                       transverse_right - track_index * self.__thread_track_width)
            self.__thread_tracks[track_index].set_metrics(track_metrics)

    def __layout_track_items(self):
        layout_indexes = self.__event_indexes.copy()
        layout_indexes.sort(key=lambda item: item.until() - item.since(), reverse=True)

        overlap_count = 0
        prev_index_area = None

        for i in range(len(self.__thread_tracks)):
            track = self.__thread_tracks[i]
            processing_indexes = layout_indexes.copy()

            for index in processing_indexes:
                bar = self.get_index_axis_item(index)
                # If this index is a single time event, it should layout at the first track
                # If track has space for this index, layout on it
                # If it's the last track, we have to layout on it
                if i == 0 and index.since() != index.until():
                    continue
                if (index.since() == index.until()) or \
                        track.has_space(*bar.get_item_metrics().get_scale_range()) or \
                        (i == len(self.__thread_tracks) - 1):
                    track.take_space_for(bar)
                    layout_indexes.remove(index)
                    bar.arrange_item(track.get_metrics())
                    index_rect = bar.get_item_metrics().rect()
                    if prev_index_area is not None and index_rect == prev_index_area:
                        overlap_count += 1
                    else:
                        overlap_count = 0
                    prev_index_area = index_rect
                    bar.shift_item(-3 * overlap_count, 0)
                else:
                    pass

    def __arrange_track_items(self):
        # for item in self.get_paint_items():
        #     item_metrics = item.get_item_metrics()
        #     item_metrics.set_scale_range(*self.get_thread_metrics().get_scale_range())
        #     item.arrange_item(item_metrics)
        paint_items = self.get_paint_items()
        for track in self.__thread_tracks:
            for bar in track.get_layout_bars():
                if bar in paint_items:
                    bar.arrange_item(track.get_metrics())


# ----------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------- class TimeAxis ---------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

class TimeAxis(QWidget):

    class Agent:
        def on_edit_record(self, record: HistoricalRecord) -> bool:
            pass

    class Scale:
        def __init__(self,
                     main_scale_offset: (int, int, int, int, int, int),
                     sub_scale_offset: (int, int, int, int, int, int)):
            assert len(main_scale_offset) == 6
            assert len(sub_scale_offset) == 6
            self.main_scale_offset = main_scale_offset
            self.sub_scale_offset = sub_scale_offset
            self.current_tick = 0

        def rough_offset_tick(self):
            return self.main_scale_offset[0] * HistoryTime.TICK_YEAR + \
                   self.main_scale_offset[0] // 4 * HistoryTime.TICK_DAY + \
                   self.main_scale_offset[1] * HistoryTime.TICK_MONTH_AVG + \
                   self.main_scale_offset[2] * HistoryTime.TICK_DAY + \
                   self.main_scale_offset[3] * HistoryTime.TICK_HOUR + \
                   self.main_scale_offset[4] * HistoryTime.TICK_MIN + \
                   self.main_scale_offset[5]

        def estimate_closest_scale(self, tick: HistoryTime.TICK) -> HistoryTime.TICK:
            date = list(HistoryTime.seconds_to_date_time(tick))
            start_suppress = False
            for i in range(len(self.main_scale_offset)):
                if self.main_scale_offset[i] == 0:
                    if start_suppress:
                        date[i] = 0 if i > 2 else 1
                else:
                    start_suppress = True
                    date[i] -= date[i] % self.main_scale_offset[i]
                if date[i] == 0 and i <= 2:
                    # year, month, day start from 1
                    date[i] = 1
            return HistoryTime.date_time_to_seconds(*date)

        def next_main_scale(self, tick: HistoryTime.TICK) -> HistoryTime.TICK:
            return HistoryTime.offset_ad_second(tick, *self.main_scale_offset)

        def next_sub_scale(self, tick: HistoryTime.TICK) -> HistoryTime.TICK:
            return HistoryTime.offset_ad_second(tick, *self.sub_scale_offset)

        def format_main_scale_text(self, tick: HistoryTime.TICK) -> str:
            formatter = [
                lambda x:'%04d' % x[0],
                lambda x:'%04d/%02d' % (x[0], x[1]),
                lambda x:'%04d/%02d/%02d' % (x[0], x[1], x[2]),

                lambda x:'%04d/%02d/%02d %02dH' % (x[0], x[1], x[2], x[3]),
                lambda x:'%04d/%02d/%02d %02d:%02d:%02d' % (x[0], x[1], x[2], x[3], x[4], x[5]),
                lambda x:'%04d/%02d/%02d %02d:%02d:%02d' % (x[0], x[1], x[2], x[3], x[4], x[5]),
            ]

            formatter_index = 0
            for index in range(len(self.main_scale_offset)):
                if self.main_scale_offset[index] != 0:
                    formatter_index = index

            date_time = list(HistoryTime.seconds_to_date_time(tick))
            year = date_time[0]
            date_time[0] = abs(year)
            date_time_text = formatter[formatter_index](date_time)

            if year < 0:
                date_time_text = 'BC' + date_time_text

            return date_time_text

    STEP_LIST = [
        Scale((10000, 0, 0, 0, 0, 0), (1000, 0, 0, 0, 0, 0)),
        Scale((5000, 0, 0, 0, 0, 0), (500, 0, 0, 0, 0, 0)),
        Scale((2500, 0, 0, 0, 0, 0), (250, 0, 0, 0, 0, 0)),
        Scale((2000, 0, 0, 0, 0, 0), (200, 0, 0, 0, 0, 0)),

        Scale((1000, 0, 0, 0, 0, 0), (100, 0, 0, 0, 0, 0)),
        Scale((500, 0, 0, 0, 0, 0), (50, 0, 0, 0, 0, 0)),
        Scale((250, 0, 0, 0, 0, 0), (25, 0, 0, 0, 0, 0)),
        Scale((200, 0, 0, 0, 0, 0), (20, 0, 0, 0, 0, 0)),

        Scale((100, 0, 0, 0, 0, 0), (10, 0, 0, 0, 0, 0)),
        Scale((50, 0, 0, 0, 0, 0), (5, 0, 0, 0, 0, 0)),
        Scale((10, 0, 0, 0, 0, 0), (1, 0, 0, 0, 0, 0)),

        Scale((1, 0, 0, 0, 0, 0), (0, 1, 0, 0, 0, 0)),
        Scale((0, 6, 0, 0, 0, 0), (0, 1, 0, 0, 0, 0)),
        Scale((0, 3, 0, 0, 0, 0), (0, 0, 15, 0, 0, 0)),
        Scale((0, 1, 0, 0, 0, 0), (0, 0, 7, 0, 0, 0)),
        Scale((0, 0, 10, 0, 0, 0), (0, 0, 1, 0, 0, 0)),

        Scale((0, 0, 1, 0, 0, 0), (0, 0, 0, 2, 0, 0)),
    ]
    # SUB_STEP_COUNT = [
    #     10, 10, 10,
    #     10, 10, 10,
    #     10, 10, 10,
    #     10, 5, 10,
    #     10, 5, 12,
    #     6, 4,
    #     7, 12,
    # ]

    DEFAULT_MARGIN_PIXEL = 0
    MAIN_SCALE_MIN_PIXEL = 50

    def __init__(self):
        super(TimeAxis, self).__init__()

        self.__agent = []

        # Paint metrics
        self.__paint_area = QRect(0, 0, 0, 0)
        self.__coordinate_metrics = AxisMetrics()

        # Axis metrics
        self.__axis_mid = 0
        self.__axis_left = 0
        self.__axis_right = 0
        self.__axis_space_w = 30
        self.__axis_align_offset = 0.4

        # Thread metrics
        self.__thread_width = 0
        self.__thread_left_area = QRect(0, 0, 0, 0)
        self.__thread_right_area = QRect(0, 0, 0, 0)

        # Scroll and Offset
        self.__offset = 0.0
        self.__scroll = 0.0
        self.__seeking = None
        self.__total_pixel_offset = None

        # Scale Step Selection
        self.__scale_selection = 0
        self.__scale = TimeAxis.STEP_LIST[8]

        self.__time_range_limit_upper = None
        self.__time_range_limit_lower = None

        self.__main_scale_limit_upper = TimeAxis.STEP_LIST[0].rough_offset_tick()
        self.__main_scale_limit_lower = TimeAxis.STEP_LIST[-1].rough_offset_tick()

        self.__scale_per_page = 10
        self.__pixel_per_scale = 0
        self.__page_tick = 0
        self.__tick_per_pixel = 0
        self.__tick_offset_mapping = AxisMapping()

        # Update flag
        self.__scale_updated = True
        self.__layout_updated = True
        self.__scroll_updated = True

        # Strictly mapping special scale to tick
        self.__optimise_pixel = {}

        self.__l_pressing = False
        self.__l_down_point = None

        # Real time tips

        self.__tip_font = QFont()
        self.__tip_font.setFamily("微软雅黑")
        self.__tip_font.setPointSize(8)

        self.__enable_real_time_tips = True
        self.__mouse_on_item = AxisItem(None, {})
        self.__mouse_on_scale_value = 0.0
        self.__mouse_on_coordinate = QPoint(0, 0)

        self.__era = ''
        self.__layout = LAYOUT_VERTICAL
        # self.__layout = LAYOUT_HORIZON

        self.set_time_range(0, 2000 * HistoryTime.TICK_YEAR)

        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setMouseTracking(True)

        self.__history_core = None
        self.__history_editor = None
        self.__history_threads = []
        self.__left_history_threads = []
        self.__right_history_threads = []

    # ----------------------------------------------------- Method -----------------------------------------------------

    # --------------------------- Sets ---------------------------

    def set_agent(self, agent: Agent):
        self.__agent.append(agent)

    def set_era(self, era: str):
        self.__era = era

    def set_axis_offset(self, offset: float):
        if 0.0 <= offset <= 1.0:
            self.__axis_align_offset = offset
        self.repaint()

    def set_time_range(self, since: HistoryTime.TICK, until: HistoryTime.TICK):
        self.auto_scale(min(since, until), max(since, until))
        self.__seeking = min(since, until)
        self.repaint()

    def set_axis_layout(self, layout: int):
        if layout in [LAYOUT_HORIZON, LAYOUT_VERTICAL]:
            self.__layout = layout
            self.repaint()

    def set_axis_scale_step(self, step: HistoryTime.TICK):
        step_index = 0
        for preset_step in TimeAxis.STEP_LIST:
            if preset_step.rough_offset_tick() <= step:
                break
            step_index += 1
        self.select_step_scale(step_index)

    def set_axis_time_range_limit(self, lower: HistoryTime.TICK, upper: HistoryTime.TICK):
        self.__time_range_limit_lower = lower
        self.__time_range_limit_upper = upper

    def set_axis_scale_step_limit(self, lower: HistoryTime.TICK, upper: HistoryTime.TICK):
        self.__main_scale_limit_lower = lower
        self.__main_scale_limit_upper = upper

    # --------------------------- Gets ---------------------------

    def get_axis_layout(self) -> int:
        return self.__layout

    def get_axis_offset(self) -> float:
        return self.__axis_align_offset

    # ------------------------- Resource -------------------------

    def set_history_core(self, history: History):
        self.__history_core = history

    def get_history_threads(self, align: int = ALIGN_RIGHT) -> list:
        return self.__left_history_threads if align == ALIGN_LEFT else self.__right_history_threads

    def add_history_thread(self, thread: TimeThreadBase, align: int = ALIGN_RIGHT,
                           base_thread: TimeThreadBase = None):
        self.remove_history_thread(thread)
        if base_thread is None or base_thread not in self.__history_threads:
            if align == ALIGN_LEFT:
                self.__left_history_threads.append(thread)
            else:
                self.__right_history_threads.append(thread)
        else:
            for i in range(0, len(self.__left_history_threads)):
                if self.__left_history_threads[i] == base_thread:
                    if align == ALIGN_LEFT:
                        self.__left_history_threads.insert(i, thread)
                    else:
                        self.__left_history_threads.insert(i + 1, thread)
            for i in range(0, len(self.__right_history_threads)):
                if self.__right_history_threads[i] == base_thread:
                    if align == ALIGN_LEFT:
                        self.__right_history_threads.insert(i, thread)
                    else:
                        self.__right_history_threads.insert(i + 1, thread)
        self.__history_threads.append(thread)
        self.__layout_updated = True
        self.repaint()

    def remove_history_thread(self, thread):
        if thread in self.__history_threads:
            self.__history_threads.remove(thread)
        if thread in self.__left_history_threads:
            self.__left_history_threads.remove(thread)
        if thread in self.__right_history_threads:
            self.__right_history_threads.remove(thread)
        self.repaint()

    def remove_all_history_threads(self):
        self.__history_threads.clear()
        self.__left_history_threads.clear()
        self.__right_history_threads.clear()
        self.repaint()

    def enable_real_time_tips(self, enable: bool):
        self.__enable_real_time_tips = enable

    def align_from_point(self, pos: QPoint) -> ALIGN_TYPE:
        if self.__layout == LAYOUT_HORIZON:
            return ALIGN_LEFT if pos.y() >= (self.__coordinate_metrics.get_transverse_length() - self.__axis_mid) else ALIGN_RIGHT
        else:
            return ALIGN_LEFT if pos.x() <= self.__axis_mid else ALIGN_RIGHT

    def thread_from_point(self, pos: QPoint) -> TimeThreadBase or None:
        for thread in self.__left_history_threads:
            if thread.get_thread_metrics().contains(pos):
                return thread
        for thread in self.__right_history_threads:
            if thread.get_thread_metrics().contains(pos):
                return thread
        return None

    def tick_from_point(self, pos: QPoint) -> HistoryTime.TICK:
        if self.__layout == LAYOUT_HORIZON:
            pixel = pos.x()
        else:
            pixel = pos.y()
        if pixel in self.__optimise_pixel.keys():
            mouse_on_scale_value = self.__optimise_pixel[pixel]
        else:
            mouse_on_scale_value = self.__coordinate_metrics.pixel_to_value(pixel)
        return mouse_on_scale_value

    # --------------------------------------------------- UI Event ----------------------------------------------------

    def wheelEvent(self, event):
        angle = event.angleDelta() / 8
        angle_x = angle.x()
        angle_y = angle.y()

        modifiers = QApplication.keyboardModifiers()

        if modifiers == QtCore.Qt.ControlModifier:
            # Get the value before step update
            current_pos = event.pos()
            pixel = current_pos.y() if self.__layout == LAYOUT_VERTICAL else current_pos.x()
            current_pos_value = self.__coordinate_metrics.pixel_to_value(pixel)

            # old_main_step = self.__main_scale
            # old_pixel_offset = current_pos_value * self.__pixel_per_scale / self.__main_scale

            self.select_step_scale(self.__scale_selection + (1 if angle_y > 0 else -1))

            self.check_update_pixel_scale()
            self.check_update_scroll_offset()

            # Make the value under mouse keep the same place on the screen
            self.__scroll = self.__tick_offset_mapping.a_to_b(current_pos_value) - pixel
            self.__offset = 0

            # print('Val = ' + str(current_pos_value) + '; Pixel = ' + str(pixel))
            # print('Step: ' + str(old_main_step) + ' -> ' + str(self.__main_scale))
            # print('Offset: ' + str(old_pixel_offset) + ' -> ' + str(value_new_offset))
        else:
            self.__scroll += (1 if angle_y < 0 else -1) * self.__pixel_per_scale / 4

        self.repaint()

    def mousePressEvent(self,  event):
        if event.button() == QtCore.Qt.LeftButton:
            self.__l_pressing = True
            self.__l_down_point = event.pos()

    def mouseReleaseEvent(self,  event):
        if event.button() == QtCore.Qt.LeftButton:
            self.__l_pressing = False
            self.__scroll += self.__offset
            self.__offset = 0
            self.repaint()
        # elif event.button() == QtCore.Qt.RightButton:
        #     for agent in self.__agent:
        #         agent.on_r_button_up(event.pos())

    def mouseDoubleClickEvent(self,  event):
        now_pos = event.pos()
        axis_item = self.axis_item_from_point(now_pos)
        if axis_item is not None:
            index = axis_item.get_index()
            if index is not None:
                self.popup_editor_for_index(index)

    def mouseMoveEvent(self, event):
        now_pos = event.pos()
        if self.__l_pressing and self.__l_down_point is not None:
            if self.__layout == LAYOUT_HORIZON:
                self.__offset = self.__l_down_point.x() - now_pos.x()
            else:
                self.__offset = self.__l_down_point.y() - now_pos.y()
            self.repaint()
        else:
            self.on_pos_updated(now_pos)

    # ----------------------------------------------------- Action -----------------------------------------------------

    def popup_editor_for_index(self, index: HistoricalRecord):
        if index is None:
            print('None index.')
            return

        # if index.get_focus_label() == 'index':
        #     source = index.source()
        #     if source is None or source == '':
        #         print('Source is empty.')
        #         return
        #     loader = HistoricalRecordLoader()
        #     if not loader.from_source(source):
        #         print('Load source error : ' + source)
        #         return
        #     records = loader.get_loaded_records()
        #     self.update_records(records)
        # else:
        #     # It's a full record
        #     records = [index]

        self.__history_editor = HistoryEditorDialog(editor_agent=self)
        self.__history_editor.get_history_editor().edit_source(index.source(), index.uuid())
        self.__history_editor.show_browser(False)

        # # To avoid lossing focus
        # self.__history_editor.setWindowFlags(Qt.Popup)
        # self.__history_editor.setAttribute(Qt.WA_QuitOnClose)
        # self.__history_editor.show()
        # self.__history_editor.raise_()
        self.__history_editor.exec_()

    # -------------------------------------------------- Calculation ---------------------------------------------------

    def check_update_paint(self):
        clock = Clock()

        self.check_update_paint_area()
        self.check_update_pixel_scale()
        self.check_update_scroll_offset()
        print('Check update: %sms' % clock.elapsed_ms())

        if self.__layout_updated or self.__scale_updated:
            clock.reset()
            self.update_thread_layout()
            print('Update thread layout: %sms' % clock.elapsed_ms())
        if self.__scale_updated or self.__scroll_updated:
            clock.reset()
            self.update_thread_scale()
            print('Update thread scale: %sms' % clock.elapsed_ms())

        self.__scale_updated = False
        self.__layout_updated = False
        self.__scroll_updated = False

    # ------------------- Check Update Param -------------------

    def check_update_paint_area(self):
        wnd_size = self.size()
        width = wnd_size.width()
        height = wnd_size.height()
        # TODO: Pixel not start from 0 (border)
        if self.__paint_area.width() != width or self.__paint_area.height() != height:
            self.__layout_updated = True
            self.__paint_area.setRect(0, 0, width, height)
            self.__coordinate_metrics.set_transverse_limit(0, height if self.__layout == LAYOUT_HORIZON else width)
            self.__coordinate_metrics.set_longitudinal_range(0, width if self.__layout == LAYOUT_HORIZON else height)

    def check_update_pixel_scale(self):
        page_pixel = self.__coordinate_metrics.get_longitudinal_length()
        if page_pixel == 0:
            return
        scale_pixel = page_pixel / self.__scale_per_page
        scale_pixel = max(scale_pixel, TimeAxis.MAIN_SCALE_MIN_PIXEL)
        scale_count = self.__coordinate_metrics.get_longitudinal_length() / scale_pixel
        rough_scale_tick = self.__scale.rough_offset_tick()
        page_tick = rough_scale_tick * scale_count

        if self.__page_tick != page_tick or self.__pixel_per_scale != scale_pixel:
            self.__scale_updated = True
            self.__page_tick = page_tick
            self.__pixel_per_scale = scale_pixel
            self.__tick_per_pixel = page_tick / page_pixel
            # Update the ratio of history-time / pixel
            self.__tick_offset_mapping.set_range_ref(page_tick, page_pixel)

    def check_update_scroll_offset(self):
        if self.__seeking is not None:
            self.__scroll = self.__tick_offset_mapping.a_to_b(self.__seeking)
            self.__offset = 0
            self.__seeking = None
        current_offset = self.__scroll + self.__offset

        # Calculate limit
        if self.__time_range_limit_upper is not None:
            limit_offset_upper = self.__tick_offset_mapping.a_to_b(self.__time_range_limit_upper)
            limit_offset_upper -= self.__coordinate_metrics.get_longitudinal_length()
            self.__scroll = min(self.__scroll, int(limit_offset_upper))
            current_offset = min(current_offset, int(limit_offset_upper))
        if self.__time_range_limit_lower is not None:
            limit_offset_lower = self.__tick_offset_mapping.a_to_b(self.__time_range_limit_lower)
            self.__scroll = max(self.__scroll, int(limit_offset_lower))
            current_offset = max(current_offset, int(limit_offset_lower))

        if self.__total_pixel_offset is None or self.__total_pixel_offset != current_offset:
            self.__scroll_updated = True
            self.__total_pixel_offset = current_offset
            tick_since = self.__tick_offset_mapping.b_to_a(self.__total_pixel_offset)
            tick_until = self.__tick_offset_mapping.b_to_a(self.__total_pixel_offset +
                                                           self.__coordinate_metrics.get_longitudinal_length())
            self.__coordinate_metrics.set_scale_range(int(tick_since), int(tick_until))

    # -------------------- Update Paint Elements --------------------

    def update_thread_layout(self):
        # Reserve the scale text width (horizon) / height (vertical) of datetime
        era_text_width = 30 if self.__layout == LAYOUT_HORIZON else 80

        left_thread_count = len(self.__left_history_threads)
        right_thread_count = len(self.__right_history_threads)
        self.__axis_mid = int(self.__coordinate_metrics.get_transverse_length() * self.__axis_align_offset)

        # TODO: Use AxisMetrics

        self.__axis_left = int(self.__axis_mid - self.__axis_space_w / 2 - 10) - era_text_width
        self.__axis_right = int(self.__axis_mid + self.__axis_space_w / 2 + 10)

        if self.__layout == LAYOUT_HORIZON:
            self.__axis_left = self.__coordinate_metrics.get_transverse_length() - self.__axis_left
            self.__axis_right = self.__coordinate_metrics.get_transverse_length() - self.__axis_right

            left_thread_width = (
                    (self.__coordinate_metrics.get_transverse_length() - self.__axis_left) / left_thread_count) if \
                left_thread_count > 0 else 0
            right_thread_width = (self.__axis_right / right_thread_count) \
                if right_thread_count > 0 else 0
        else:
            left_thread_width = self.__axis_left / left_thread_count if left_thread_count > 0 else 0
            right_thread_width = (
                    (self.__coordinate_metrics.get_transverse_length() - self.__axis_right) / right_thread_count) \
                if right_thread_count > 0 else 0

        # Vertical -> Horizon : Left rotate

        for i in range(0, left_thread_count):
            thread = self.__left_history_threads[i]

            metrics = AxisMetrics()
            metrics.set_align(ALIGN_LEFT)
            metrics.set_layout(self.__layout)

            top = TimeAxis.DEFAULT_MARGIN_PIXEL
            bottom = self.__coordinate_metrics.get_longitudinal_length() - TimeAxis.DEFAULT_MARGIN_PIXEL
            if self.__layout == LAYOUT_HORIZON:
                # TODO: Can we just rotate the QPaint axis?
                left = self.__coordinate_metrics.get_transverse_length() - i * left_thread_width
                right = left - left_thread_width
            else:
                left = i * left_thread_width
                right = left + left_thread_width

            metrics.set_transverse_limit(left, right)
            metrics.set_longitudinal_range(top, bottom)
            metrics.set_scale_range(*self.__coordinate_metrics.get_scale_range())
            thread.set_thread_metrics(metrics)
            thread.refresh()

        for i in range(0, right_thread_count):
            thread = self.__right_history_threads[i]

            metrics = AxisMetrics()
            metrics.set_align(ALIGN_RIGHT)
            metrics.set_layout(self.__layout)

            top = TimeAxis.DEFAULT_MARGIN_PIXEL
            bottom = self.__coordinate_metrics.get_longitudinal_length() - TimeAxis.DEFAULT_MARGIN_PIXEL
            if self.__layout == LAYOUT_HORIZON:
                # TODO: Can we just rotate the QPaint axis?
                left = self.__axis_right - i * right_thread_width
                right = left - right_thread_width
            else:
                left = self.__axis_right + i * right_thread_width
                right = left + right_thread_width
            metrics.set_transverse_limit(left, right)
            metrics.set_longitudinal_range(top, bottom)
            metrics.set_scale_range(*self.__coordinate_metrics.get_scale_range())
            thread.set_thread_metrics(metrics)
            thread.refresh()

    def update_thread_scale(self):
        for thread in self.__history_threads:
            thread.get_thread_metrics().set_scale_range(*self.__coordinate_metrics.get_scale_range())
            thread.refresh()

    # ----------------------------------------------------- Paint ------------------------------------------------------

    def paintEvent(self, event):
        print('--------------------------------------------------------------------------------------')

        clock = Clock()
        start = time.process_time()

        qp = QPainter()
        qp.begin(self)

        self.check_update_paint()

        clock.reset()
        self.paint_background(qp)
        if self.__layout == LAYOUT_HORIZON:
            self.paint_horizon_scale(qp)
        else:
            self.paint_vertical_scale(qp)
        print('Paint axis: %sms' % clock.elapsed_ms())

        clock.reset()
        self.paint_threads(qp)
        print('Paint threads: %sms' % clock.elapsed_ms())

        clock.reset()
        self.paint_real_time_tips(qp)
        print('Paint real time tips: %sms' % clock.elapsed_ms())

        qp.end()

        end = time.process_time()

        # print('Offset = %s, Step = %s; Pixel = %s, Value = %s' %
        #       (self.__scroll + self.__offset, self.__main_scale,
        #        self.__mouse_on_coordinate.y(), self.__mouse_on_scale_value))
        print('------------------- Axis paint spends time: %ss -------------------' % (end - start))

    def paint_background(self, qp: QPainter):
        qp.setBrush(AXIS_BACKGROUND_COLORS[2])
        qp.drawRect(self.__paint_area)

    def paint_horizon_scale(self, qp: QPainter):
        qp.drawLine(0, self.__paint_area.height() - self.__axis_mid,
                    self.__paint_area.width(), self.__paint_area.height() - self.__axis_mid)

        # self.__coordinate_metrics.get_longitudinal_range()

        main_scale_start = self.__paint_area.height() - int(self.__axis_mid + 15)
        main_scale_end = self.__paint_area.height() - int(self.__axis_mid - 15)
        sub_scale_start = self.__paint_area.height() - int(self.__axis_mid + 5)
        sub_scale_end = self.__paint_area.height() - int(self.__axis_mid - 5)

        self.__optimise_pixel.clear()

        tick_since, tick_until = self.__coordinate_metrics.get_scale_range()
        paint_tick = self.__scale.estimate_closest_scale(int(tick_since))
        assert paint_tick <= tick_since

        while paint_tick < tick_until:
            next_paint_tick = self.__scale.next_main_scale(paint_tick)

            x_main = int(self.__coordinate_metrics.value_to_pixel(int(paint_tick)))
            self.__optimise_pixel[x_main] = paint_tick
            main_scale_text = self.__scale.format_main_scale_text(paint_tick)

            qp.drawLine(x_main, main_scale_start, x_main, main_scale_end)
            qp.drawText(x_main, main_scale_end + 20, main_scale_text)

            # print("Main: " + str(HistoryTime.seconds_to_date_time(paint_tick)))

            # clock = Clock()
            while True:
                prev_paint_tick = paint_tick
                paint_tick = self.__scale.next_sub_scale(paint_tick)
                delta_paint_tick = paint_tick - prev_paint_tick

                if paint_tick >= next_paint_tick or (next_paint_tick - paint_tick) / delta_paint_tick < 0.5:
                    break

                # print("    Sub: " + str(HistoryTime.seconds_to_date_time(paint_tick)))
                x_sub = int(self.__coordinate_metrics.value_to_pixel(int(paint_tick)))
                self.__optimise_pixel[x_sub] = paint_tick
                qp.drawLine(x_sub, sub_scale_start, x_sub, sub_scale_end)
            # print('Paint sub scale: %sms' % clock.elapsed_ms())

            paint_tick = next_paint_tick

        # for i in range(0, 12):
        #     time_main = self.__paint_start_tick + i * self.__main_scale
        #     x_main = int(self.__coordinate_metrics.value_to_pixel(int(time_main)))
        #
        #     self.__optimise_pixel[x_main] = time_main
        #
        #     if self.__main_scale >= HistoryTime.year(1):
        #         main_scale_text = HistoryTime.tick_to_standard_string(time_main)
        #     else:
        #         main_scale_text = HistoryTime.tick_to_standard_string(time_main, show_date=True)
        #
        #     qp.drawLine(x_main, main_scale_start, x_main, main_scale_end)
        #     qp.drawText(x_main, main_scale_end + 20, main_scale_text)
        #
        #     for j in range(0, self.__sub_scale_count):
        #         time_sub = time_main + self.__main_scale * j / self.__sub_scale_count
        #         x_sub = int(self.__coordinate_metrics.value_to_pixel(int(time_sub)))
        #         self.__optimise_pixel[x_sub] = time_sub
        #         qp.drawLine(x_sub, sub_scale_start, x_sub, sub_scale_end)

    def paint_vertical_scale(self, qp: QPainter):
        qp.drawLine(self.__axis_mid, 0, self.__axis_mid, self.__paint_area.height())

        main_scale_start = int(self.__axis_mid - 15)
        main_scale_end = int(self.__axis_mid + 15)
        sub_scale_start = int(self.__axis_mid - 5)
        sub_scale_end = int(self.__axis_mid + 5)

        self.__optimise_pixel.clear()

        tick_since, tick_until = self.__coordinate_metrics.get_scale_range()
        paint_tick = self.__scale.estimate_closest_scale(int(tick_since))
        assert paint_tick <= tick_since

        while paint_tick < tick_until:
            next_paint_tick = self.__scale.next_main_scale(paint_tick)

            y_main = int(self.__coordinate_metrics.value_to_pixel(paint_tick))
            self.__optimise_pixel[y_main] = paint_tick
            main_scale_text = self.__scale.format_main_scale_text(paint_tick)

            qp.drawLine(main_scale_start, y_main, main_scale_end, y_main)
            qp.drawText(main_scale_end - 100, y_main, main_scale_text)

            # print("Main: " + str(HistoryTime.seconds_to_date_time(paint_tick)))

            while True:
                prev_paint_tick = paint_tick
                paint_tick = self.__scale.next_sub_scale(paint_tick)
                delta_paint_tick = paint_tick - prev_paint_tick

                if paint_tick >= next_paint_tick or (next_paint_tick - paint_tick) / delta_paint_tick < 0.5:
                    break

                # print("    Sub: " + str(HistoryTime.seconds_to_date_time(paint_tick)))
                y_sub = int(self.__coordinate_metrics.value_to_pixel(int(paint_tick)))
                self.__optimise_pixel[y_sub] = paint_tick
                qp.drawLine(sub_scale_start, y_sub, sub_scale_end, y_sub)

            paint_tick = next_paint_tick

        # for i in range(0, 12):
        #     time_main = self.__paint_start_tick + i * self.__main_scale
        #     y_main = int(self.__coordinate_metrics.value_to_pixel(int(time_main)))
        #
        #     self.__optimise_pixel[y_main] = time_main
        #
        #     # original_year = HistoryTime.year_of_tick(time_main)
        #     # retrieve_tick = self.pixel_to_value(y_main)
        #     # retrieve_year = HistoryTime.year_of_tick(retrieve_tick)
        #     # print(str(time_main) + '(' + str(original_year) + ') -> ' + str(y_main) + ' -> ' +
        #     #       str(retrieve_tick) + '(' + str(retrieve_year) + ')')
        #
        #     if self.__main_scale >= HistoryTime.year(1):
        #         main_scale_text = HistoryTime.tick_to_standard_string(time_main)
        #     else:
        #         main_scale_text = HistoryTime.tick_to_standard_string(time_main, show_date=True)
        #
        #     qp.drawLine(main_scale_start, y_main, main_scale_end, y_main)
        #     qp.drawText(main_scale_end - 100, y_main, main_scale_text)
        #
        #     for j in range(0, self.__sub_scale_count):
        #         time_sub = time_main + self.__main_scale * j / self.__sub_scale_count
        #         y_sub = int(self.__coordinate_metrics.value_to_pixel(int(time_sub)))
        #         self.__optimise_pixel[y_sub] = time_sub
        #         qp.drawLine(sub_scale_start, y_sub, sub_scale_end, y_sub)

    def paint_threads(self, qp: QPainter):
        for thread in self.__history_threads:
            thread.paint(qp)

    def paint_real_time_tips(self, qp: QPainter):
        if not self.__enable_real_time_tips or self.__l_pressing:
            return

        qp.setPen(QColor(0, 0, 0))

        qp.drawLine(0, self.__mouse_on_coordinate.y(), self.__paint_area.width(), self.__mouse_on_coordinate.y())
        qp.drawLine(self.__mouse_on_coordinate.x(), 0, self.__mouse_on_coordinate.x(), self.__paint_area.height())

        tip_text = self.format_real_time_tip()

        fm = QFontMetrics(self.__tip_font)
        text_width = fm.width(tip_text)
        text_height = fm.height()
        tip_area = QRect(self.__mouse_on_coordinate, QSize(text_width, text_height))

        tip_area.setTop(tip_area.top() - fm.height())
        tip_area.setBottom(tip_area.bottom() - fm.height())
        if tip_area.right() > self.__coordinate_metrics.get_transverse_length():
            tip_area.setLeft(tip_area.left() - text_width)
            tip_area.setRight(tip_area.right() - text_width)

        qp.setFont(self.__tip_font)
        qp.setBrush(QColor(36, 169, 225))

        qp.drawRect(tip_area)
        qp.drawText(tip_area, Qt.AlignLeft, tip_text)

    # ----------------------------------------------------- Scale ------------------------------------------------------

    def auto_scale(self, since: HistoryTime.TICK, until: HistoryTime.TICK):
        # since_rough = lower_rough(since)
        # until_rough = upper_rough(until)
        # delta = until_rough - since_rough
        # delta_rough = upper_rough(delta)
        step_rough = abs(until - since) / 10

        step_index = 1
        while step_index < len(TimeAxis.STEP_LIST):
            if TimeAxis.STEP_LIST[step_index].rough_offset_tick() < step_rough:
                break
            step_index += 1
        self.select_step_scale(step_index - 1)
        self.check_update_pixel_scale()

    def select_step_scale(self, scale_index: int):
        scale_index = max(scale_index, 0)
        scale_index = min(scale_index, len(TimeAxis.STEP_LIST) - 1)
        new_scale = TimeAxis.STEP_LIST[scale_index]

        if self.__main_scale_limit_lower <= new_scale.rough_offset_tick() <= self.__main_scale_limit_upper:
            self.__scale = new_scale
            self.__scale_selection = scale_index
        #     self.__sub_scale_count = TimeAxis.SUB_STEP_COUNT[self.__scale_selection]
        # self.__main_scale = max(self.__main_scale, self.__main_scale_limit_lower)
        # self.__main_scale = min(self.__main_scale, self.__main_scale_limit_upper)

    def axis_item_from_point(self, point: QPoint) -> AxisItem or None:
        thread = self.thread_from_point(point)
        if thread is not None:
            return thread.axis_item_from_point(point)

    def calc_point_to_paint_start_offset(self, point):
        if self.__layout == LAYOUT_HORIZON:
            return point.x() - TimeAxis.DEFAULT_MARGIN_PIXEL
        else:
            return point.y() - TimeAxis.DEFAULT_MARGIN_PIXEL

    # def value_to_pixel(self, value: int, from_origin: bool = False) -> float:
    #     return float(value - self.__total_tick_offset) / self.__main_scale * self.__pixel_per_scale \
    #            if not from_origin else value / self.__main_scale * self.__pixel_per_scale
    #
    # def pixel_to_value(self, pixel: int) -> float:
    #     if pixel in self.__optimise_pixel.keys():
    #         return self.__optimise_pixel[pixel]
    #     else:
    #         return float(pixel) / self.__pixel_per_scale * self.__main_scale + self.__total_tick_offset

    # ------------------------------------------ Art ------------------------------------------

    def format_real_time_tip(self) -> str:
        # Show The Time From Mouse Position
        year, month, day, _ = HistoryTime.seconds_to_date(int(self.__mouse_on_scale_value))
        tip_text = '(' + str(year) + ')'

        # Axis Item information
        if self.__mouse_on_item is not None:
            item_tip = self.__mouse_on_item.get_tip_text(self.__mouse_on_scale_value)
            if len(item_tip) > 0:
                tip_text += ' | '
                tip_text += item_tip
        return tip_text

    # ------------------------------------- Real Time Tips ------------------------------------

    def on_pos_updated(self, pos: QPoint):
        if not self.__enable_real_time_tips:
            return
        if self.__mouse_on_coordinate != pos:
            self.__mouse_on_coordinate = pos
            self.__mouse_on_scale_value = self.tick_from_point(pos)
            self.__mouse_on_item = self.axis_item_from_point(pos)
            self.repaint()

    # ------------------------------- HistoryRecordEditor.Agent -------------------------------

    def on_apply(self):
        if self.__history_editor is None:
            print('Unexpected Error: History editor is None.')
            return

        records = self.__history_editor.get_history_editor().get_records()

        if records is None or len(records) == 0:
            return

        indexer = HistoricalRecordIndexer()
        indexer.index_records(records)
        indexes = indexer.get_indexes()

        # TODO: Maybe we should named it as update_*()
        self.__history_core.update_records(records)
        self.__history_core.update_indexes(indexes)

        self.__history_editor.on_apply()
        self.__history_editor.close()

        self.repaint()

    def on_cancel(self):
        if self.__history_editor is not None:
            self.__history_editor.close()
        else:
            print('Unexpected Error: History editor is None.')


# ----------------------------------------------------------------------------------------------------------------------
# --------------------------------------------- class HistoryViewerDialog ----------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

class HistoryViewerDialog(QDialog):
    def __init__(self):
        super(HistoryViewerDialog, self).__init__()

        self.time_axis = TimeAxis()
        layout = QVBoxLayout()
        layout.addWidget(self.time_axis)

        self.setLayout(layout)
        self.setWindowFlags(self.windowFlags() |
                            Qt.WindowMinMaxButtonsHint |
                            QtCore.Qt.WindowSystemMenuHint)

    def get_time_axis(self) -> TimeAxis:
        return self.time_axis


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    app = QApplication(sys.argv)

    # Indexer
    indexer = HistoricalRecordIndexer()
    indexer.load_from_file('depot/history.index')
    indexer.print_indexes()

    # Threads
    thread = HistoryIndexTrack()
    thread.set_thread_color(THREAD_BACKGROUND_COLORS[0])
    thread.set_thread_event_indexes(indexer.get_indexes())

    # History
    history = History()
    history.update_indexes(indexer.get_indexes())

    # HistoryViewerDialog
    history_viewer = HistoryViewerDialog()
    history_viewer.get_time_axis().set_history_core(history)
    history_viewer.get_time_axis().add_history_thread(thread)
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










