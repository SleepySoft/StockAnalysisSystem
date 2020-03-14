import copy
import time
import random
import traceback, math

from PyQt5.QtCore import QRect, QPoint, QSize
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QPolygon, QFontMetrics

from editor import *
from Utility.ui_utility import *
from Utility.viewer_utility import *
from Utility.history_public import *


# ------------------------------------------------------ AxisItem ------------------------------------------------------

class AxisItem:
    def __init__(self, index: HistoricalRecord, extra: dict):
        self.extra = extra
        self.index = index
        self.item_metrics = AxisMetrics()
        self.outer_metrics = AxisMetrics()

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

        since_pixel = outer_metrics.value_to_pixel(self.index.since())
        until_pixel = outer_metrics.value_to_pixel(self.index.until())
        outer_since, outer_until = outer_metrics.get_longitudinal_range()
        self.item_metrics.set_scale_range(self.index.since(), self.index.until())
        self.item_metrics.set_longitudinal_range(max(since_pixel, outer_since), min(until_pixel, outer_until))

    def paint(self, qp: QPainter):
        assert False


# ----------------------------------------------------------------------------------------------------------------------
#                                                  class TimeTrackBar
# ----------------------------------------------------------------------------------------------------------------------

event_font = QFont()
event_font.setFamily("微软雅黑")
event_font.setPointSize(6)

period_font = QFont()
period_font.setFamily("微软雅黑")
period_font.setPointSize(8)


class TimeTrackBar(AxisItem):
    def __init__(self, index: HistoricalRecord, extra: dict = {}):
        super(TimeTrackBar, self).__init__(index, extra)
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
            tip_text += ' : [' + str(HistoryTime.year_of_tick(since)) + ']'
        else:
            # If it's a period event.
            since_year = HistoryTime.year_of_tick(since)
            current_year = HistoryTime.year_of_tick(on_tick)
            until_year = HistoryTime.year_of_tick(until)

            # Show Current Year / Total Year
            tip_text += '(' + str(current_year - since_year)
            tip_text += '/' + str(HistoryTime.year_of_tick(until - since)) + ')'

            # Show Period
            tip_text += ' : [' + str(since_year) + ' - ' + str(until_year) + ']'
        return tip_text

    def paint(self, qp: QPainter):
        if self.get_outer_metrics().get_layout() == LAYOUT_HORIZON:
            self.__paint_horizon(qp)
        elif self.get_outer_metrics().get_layout() == LAYOUT_VERTICAL:
            self.__paint_vertical(qp)

    def arrange_item(self, outer_metrics: AxisMetrics):
        super(TimeTrackBar, self).arrange_item(outer_metrics)

        if self.index.since() == self.index.until():
            outer_left, outer_right = outer_metrics.get_transverse_limit()
            diagonal = abs(outer_right - outer_left)
            half_diagonal = diagonal / 2
            since_pixel, until_pixel = self.get_item_metrics().get_longitudinal_range()
            since_pixel -= abs(half_diagonal)
            until_pixel += abs(half_diagonal)
            outer_since, outer_until = outer_metrics.get_longitudinal_range()
            self.item_metrics.set_longitudinal_range(max(since_pixel, outer_since), min(until_pixel, outer_until))

    def __paint_horizon(self, qp: QPainter):
        metrics = self.get_item_metrics()
        if self.get_index().since() == self.get_index().until():
            TimeTrackBar.paint_event_bar_horizon(qp, metrics.rect(), self.__event_bk, metrics.get_align())
            TimeTrackBar.paint_index_text(qp, self.get_index(), metrics.rect(), event_font)
        else:
            TimeTrackBar.paint_period_bar(qp, metrics.rect(), self.__story_bk)
            TimeTrackBar.paint_index_text(qp, self.get_index(), metrics.rect(), period_font)

    def __paint_vertical(self, qp: QPainter):
        metrics = self.get_item_metrics()
        if self.get_index().since() == self.get_index().until():
            TimeTrackBar.paint_event_bar_vertical(qp, metrics.rect(), self.__event_bk, metrics.get_align())
            TimeTrackBar.paint_index_text(qp, self.get_index(), metrics.rect(), event_font)
        else:
            TimeTrackBar.paint_period_bar(qp, metrics.rect(), self.__story_bk)
            TimeTrackBar.paint_index_text(qp, self.get_index(), metrics.rect(), period_font)

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

        abstract_tags = index.get_tags('abstract')
        abstract = abstract_tags[0] if len(abstract_tags) > 0 else ''
        qp.drawText(index_rect, Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextWordWrap, abstract)
        # qp.restore()


# ----------------------------------------------------------------------------------------------------------------------
#                                                 class TimeThreadBase
# ----------------------------------------------------------------------------------------------------------------------

class TimeThreadBase:
    REFERENCE_TRACK_WIDTH = 50

    def __init__(self):
        self.__event_indexes = []
        self.__paint_indexes = []
        self.__index_bar_table = {}

        self.__thread_track = []
        self.__thread_track_bars = []

        self.__metrics = AxisMetrics()
        self.__min_track_width = TimeThreadBase.REFERENCE_TRACK_WIDTH
        self.__thread_track_count = 0
        self.__thread_track_width = 50

        self.__paint_color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    # ------------------------------------------- Operations -------------------------------------------

    def paint(self, qp: QPainter):
        qp.setBrush(self.__paint_color)
        qp.drawRect(self.__metrics.rect())

        if self.__metrics.get_layout() == LAYOUT_HORIZON:
            self.__paint_horizon(qp)
        elif self.__metrics.get_layout() == LAYOUT_VERTICAL:
            self.__paint_vertical(qp)
        else:
            assert False

    def refresh(self):
        # When scale updated
        self.__pickup_paint_indexes()
        # When metrics updated
        self.__calc_paint_parameters()
        self.__layout_track()
        self.__layout_bars()

    def axis_item_from_point(self, point: QPoint) -> AxisItem or None:
        if not self.get_thread_metrics().contains(point):
            return None
        for i in range(len(self.__thread_track_bars) - 1, -1, -1):
            axis_item = self.__thread_track_bars[i]
            if axis_item.get_item_metrics().contains(point):
                return axis_item
        return None

    # ------------------------------------------ Sets ------------------------------------------

    def set_thread_metrics(self, metrics: AxisMetrics):
        # Use copy instead of assignment.
        # # So the reference in bar also updated.
        self.__metrics.copy(metrics)

    def set_thread_min_track_width(self, width: int):
        self.__min_track_width = width

    def set_thread_event_indexes(self, indexes: list):
        self.__event_indexes = indexes
        self.__index_bar_table.clear()

    # ------------------------------------------ Gets ------------------------------------------

    def set_thread_color(self, color: QColor):
        self.__paint_color = color

    def get_thread_metrics(self) -> AxisMetrics:
        return self.__metrics

    def get_index_bar(self, index: HistoricalRecord) -> TimeTrackBar:
        bar = self.__index_bar_table.get(index, None)
        if bar is None:
            bar = TimeTrackBar(index)
            self.__index_bar_table[index] = bar
        return bar

    # ------------------------------------------------------------------------------------------

    def __pickup_paint_indexes(self):
        self.__paint_indexes.clear()
        since, until = self.__metrics.get_scale_range()
        for index in self.__event_indexes:
            if index.period_adapt(since, until):
                # Pick the paint indexes and sort by its period length
                self.__paint_indexes.append(index)

        # Sort method 1: The earlier index has higher priority -> The start track would be full filled.
        # self.__paint_indexes = sorted(self.__paint_indexes, key=lambda x: x.since())

        # Sort method2: The longer index has higher priority -> The bar layout should be more stable.
        self.__paint_indexes.sort(key=lambda item: item.until() - item.since(), reverse=True)

    def __calc_paint_parameters(self):
        # Adjust track count
        self.__thread_track_count = self.__metrics.wide() / self.__min_track_width
        self.__thread_track_count = max(1, int(self.__thread_track_count + 0.5))
        self.__thread_track_width = self.__metrics.wide() / self.__thread_track_count

    def __layout_track(self):
        self.__thread_track.clear()

        for track_index in range(0, self.__thread_track_count):
            track_metrics = copy.deepcopy(self.__metrics)
            transverse_left, transverse_right = self.__metrics.get_transverse_limit()

            # TODO: How to do it with the same inteface
            if self.__metrics.get_layout() == LAYOUT_HORIZON:
                if self.__metrics.get_align() == ALIGN_RIGHT:
                    track_metrics.set_transverse_limit(transverse_left - track_index * self.__thread_track_width,
                                                       transverse_left - (track_index + 1) * self.__thread_track_width)
                else:
                    track_metrics.set_transverse_limit(transverse_right + (track_index + 1) * self.__thread_track_width,
                                                       transverse_right + track_index * self.__thread_track_width)
            else:
                if self.__metrics.get_align() == ALIGN_RIGHT:
                    track_metrics.set_transverse_limit(transverse_left + track_index * self.__thread_track_width,
                                                       transverse_left + (track_index + 1) * self.__thread_track_width)
                else:
                    track_metrics.set_transverse_limit(transverse_right - (track_index + 1) * self.__thread_track_width,
                                                       transverse_right - track_index * self.__thread_track_width)
            track = TrackContext()
            track.set_metrics(track_metrics)
            self.__thread_track.append(track)

    def __layout_bars(self):
        self.__thread_track_bars.clear()
        layout_indexes = self.__paint_indexes.copy()

        overlap_count = 0
        prev_index_area = None

        for i in range(0, len(self.__thread_track)):
            track = self.__thread_track[i]

            processing_indexes = layout_indexes.copy()
            for index in processing_indexes:
                bar = self.get_index_bar(index)
                # If this index is a single time event, it should layout at the first track
                # If track has space for this index, layout on it
                # If it's the last track, we have to layout on it
                if i == 0 and index.since() != index.until():
                    continue
                if (index.since() == index.until()) or \
                        track.has_space(*bar.get_item_metrics().get_longitudinal_range()) or \
                        (i == len(self.__thread_track) - 1):
                    track.take_space_for(bar)
                    bar.arrange_item(track.get_metrics())
                    layout_indexes.remove(index)
                    self.__thread_track_bars.append(bar)

                    index_rect = bar.get_item_metrics().rect()
                    if prev_index_area is not None and index_rect == prev_index_area:
                        overlap_count += 1
                    else:
                        overlap_count = 0
                    prev_index_area = index_rect
                    bar.shift_item(-3 * overlap_count, 0)

    def __paint_horizon(self, qp: QPainter):
        for bar in self.__thread_track_bars:
            bar.paint(qp)

    def __paint_vertical(self, qp: QPainter):
        for bar in self.__thread_track_bars:
            bar.paint(qp)


# --------------------------------------------------- class TimeAxis ---------------------------------------------------

class TimeAxis(QWidget):

    class Agent:
        def __init__(self):
            pass

        def on_r_button_up(self, pos: QPoint):
            pass

    STEP_LIST = [
        HistoryTime.year(10000), HistoryTime.year(5000), HistoryTime.year(2500),
        HistoryTime.year(2000), HistoryTime.year(1000), HistoryTime.year(500),
        HistoryTime.year(250), HistoryTime.year(200), HistoryTime.year(100),
        HistoryTime.year(50), HistoryTime.year(25), HistoryTime.year(20),
        HistoryTime.year(10), HistoryTime.year(5), HistoryTime.year(1),
        HistoryTime.month(6), HistoryTime.month(1),
        HistoryTime.week(1), HistoryTime.day(1),
    ]
    SUB_STEP_COUNT = [
        10, 10, 10,
        10, 10, 10,
        10, 10, 10,
        10, 5, 10,
        10, 5, 12,
        6, 4,
        7, 12,
    ]

    DEFAULT_MARGIN_PIXEL = 0
    MAIN_SCALE_MIN_PIXEL = 50

    def __init__(self):
        super(TimeAxis, self).__init__()

        self.__agent = []
        self.__width = 0
        self.__height = 0
        self.__axis_width = 0
        self.__axis_length = 0

        self.__axis_area = QRect(0, 0, 0, 0)
        self.__paint_area = QRect(0, 0, 0, 0)

        self.__axis_mid = 0
        self.__axis_left = 0
        self.__axis_right = 0
        self.__axis_space_w = 30
        self.__axis_align_offset = 0.4

        self.__thread_width = 0
        self.__thread_left_area = QRect(0, 0, 0, 0)
        self.__thread_right_area = QRect(0, 0, 0, 0)

        self.__offset = 0.0
        self.__scroll = 0.0

        self.__scale_per_page = 10

        self.__pixel_per_scale = 0
        self.__total_tick_offset = 0
        self.__total_pixel_offset = 0

        self.__paint_since_scale = 0
        self.__paint_until_scale = 0

        self.__paint_start_scale = 0
        self.__paint_start_tick = 0

        # self.__axis_metrics = AxisMetrics()

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

        self.__step_selection = 0
        self.__main_step = TimeAxis.STEP_LIST[0]
        self.__sub_step_count = 10

        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

        self.set_time_range(0, HistoryTime.year(2000))

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

    def set_time_range(self, since: float, until: float):
        self.auto_scale(min(since, until), max(since, until))
        self.repaint()

    def set_axis_layout(self, layout: int):
        if layout in [LAYOUT_HORIZON, LAYOUT_VERTICAL]:
            self.__layout = layout
            self.repaint()

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
            return ALIGN_LEFT if pos.y() >= (self.__axis_width - self.__axis_mid) else ALIGN_RIGHT
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
            current_pos_value = self.pixel_to_value(pixel)

            old_main_step = self.__main_step
            old_pixel_offset = current_pos_value * self.__pixel_per_scale / self.__main_step

            self.select_step_scale(self.__step_selection + (1 if angle_y > 0 else -1))
            # Make the value under mouse keep the same place on the screen
            value_new_offset = current_pos_value * self.__pixel_per_scale / self.__main_step
            self.__scroll = int(value_new_offset - pixel)
            self.__offset = 0

            # print('Val = ' + str(current_pos_value) + '; Pixel = ' + str(pixel))
            # print('Step: ' + str(old_main_step) + ' -> ' + str(self.__main_step))
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
        elif event.button() == QtCore.Qt.RightButton:
            for agent in self.__agent:
                agent.on_r_button_up(event.pos())

    def mouseDoubleClickEvent(self,  event):
        now_pos = event.pos()
        axis_item = self.axis_item_from_point(now_pos)
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
        self.__history_editor.exec()

    # ----------------------------------------------------- Paint ------------------------------------------------------

    def paintEvent(self, event):
        start = time.process_time()

        qp = QPainter()
        qp.begin(self)

        self.update_paint_area()
        self.update_pixel_per_scale()
        self.calc_paint_parameters()
        self.calc_paint_layout()

        self.paint_background(qp)

        if self.__layout == LAYOUT_HORIZON:
            self.paint_horizon(qp)
        else:
            self.paint_vertical(qp)
        self.paint_threads(qp)
        self.paint_real_time_tips(qp)

        qp.end()

        end = time.process_time()

        # print('Offset = %s, Step = %s; Pixel = %s, Value = %s' %
        #       (self.__scroll + self.__offset, self.__main_step,
        #        self.__mouse_on_coordinate.y(), self.__mouse_on_scale_value))
        print('Axis paint spends time: %s s' % (end - start))

    def paint_background(self, qp: QPainter):
        qp.setBrush(AXIS_BACKGROUND_COLORS[2])
        qp.drawRect(0, 0, self.__width, self.__height)

    def paint_horizon(self, qp: QPainter):
        qp.drawLine(0, self.__height - self.__axis_mid, self.__width, self.__height - self.__axis_mid)

        main_scale_start = self.__height - int(self.__axis_mid + 15)
        main_scale_end = self.__height - int(self.__axis_mid - 15)
        sub_scale_start = self.__height - int(self.__axis_mid + 5)
        sub_scale_end = self.__height - int(self.__axis_mid - 5)

        self.__optimise_pixel.clear()

        for i in range(0, 12):
            time_main = self.__paint_start_tick + i * self.__main_step
            x_main = int(self.value_to_pixel(int(time_main)))

            self.__optimise_pixel[x_main] = time_main

            if self.__main_step >= HistoryTime.year(1):
                main_scale_text = HistoryTime.tick_to_standard_string(time_main)
            else:
                main_scale_text = HistoryTime.tick_to_standard_string(time_main, show_date=True)

            qp.drawLine(x_main, main_scale_start, x_main, main_scale_end)
            qp.drawText(x_main, main_scale_end + 20, main_scale_text)

            for j in range(0, self.__sub_step_count):
                time_sub = time_main + self.__main_step * j / self.__sub_step_count
                x_sub = int(self.value_to_pixel(int(time_sub)))
                self.__optimise_pixel[x_sub] = time_sub
                qp.drawLine(x_sub, sub_scale_start, x_sub, sub_scale_end)

    def paint_vertical(self, qp: QPainter):
        qp.drawLine(self.__axis_mid, 0, self.__axis_mid, self.__height)

        main_scale_start = int(self.__axis_mid - 15)
        main_scale_end = int(self.__axis_mid + 15)
        sub_scale_start = int(self.__axis_mid - 5)
        sub_scale_end = int(self.__axis_mid + 5)

        self.__optimise_pixel.clear()

        for i in range(0, 12):
            time_main = self.__paint_start_tick + i * self.__main_step
            y_main = int(self.value_to_pixel(int(time_main)))

            self.__optimise_pixel[y_main] = time_main

            # original_year = HistoryTime.year_of_tick(time_main)
            # retrieve_tick = self.pixel_to_value(y_main)
            # retrieve_year = HistoryTime.year_of_tick(retrieve_tick)
            # print(str(time_main) + '(' + str(original_year) + ') -> ' + str(y_main) + ' -> ' +
            #       str(retrieve_tick) + '(' + str(retrieve_year) + ')')

            if self.__main_step >= HistoryTime.year(1):
                main_scale_text = HistoryTime.tick_to_standard_string(time_main)
            else:
                main_scale_text = HistoryTime.tick_to_standard_string(time_main, show_date=True)

            qp.drawLine(main_scale_start, y_main, main_scale_end, y_main)
            qp.drawText(main_scale_end - 100, y_main, main_scale_text)

            for j in range(0, self.__sub_step_count):
                time_sub = time_main + self.__main_step * j / self.__sub_step_count
                y_sub = int(self.value_to_pixel(int(time_sub)))
                self.__optimise_pixel[y_sub] = time_sub
                qp.drawLine(sub_scale_start, y_sub, sub_scale_end, y_sub)

    def paint_threads(self, qp: QPainter):
        for thread in self.__history_threads:
            thread.paint(qp)

    def paint_real_time_tips(self, qp: QPainter):
        if not self.__enable_real_time_tips or self.__l_pressing:
            return

        qp.drawLine(0, self.__mouse_on_coordinate.y(), self.__width, self.__mouse_on_coordinate.y())
        qp.drawLine(self.__mouse_on_coordinate.x(), 0, self.__mouse_on_coordinate.x(), self.__height)

        tip_text = self.format_real_time_tip()

        fm = QFontMetrics(self.__tip_font)
        text_width = fm.width(tip_text)
        text_height = fm.height()
        tip_area = QRect(self.__mouse_on_coordinate, QSize(text_width, text_height))

        tip_area.setTop(tip_area.top() - fm.height())
        tip_area.setBottom(tip_area.bottom() - fm.height())
        if tip_area.right() > self.__axis_width:
            tip_area.setLeft(tip_area.left() - text_width)
            tip_area.setRight(tip_area.right() - text_width)

        qp.setFont(self.__tip_font)
        qp.setBrush(QColor(36, 169, 225))

        qp.drawRect(tip_area)
        qp.drawText(tip_area, Qt.AlignLeft, tip_text)

    # -------------------------------------------------- Calculation ---------------------------------------------------

    def axis_item_from_point(self, point: QPoint) -> AxisItem or None:
        thread = self.thread_from_point(point)
        if thread is not None:
            return thread.axis_item_from_point(point)
        # for thread in self.__history_threads:
        #     axis_item = thread.axis_item_from_point(point)
        #     if axis_item is not None:
        #         return axis_item
        # return None

    def calc_point_to_paint_start_offset(self, point):
        if self.__layout == LAYOUT_HORIZON:
            return point.x() - TimeAxis.DEFAULT_MARGIN_PIXEL
        else:
            return point.y() - TimeAxis.DEFAULT_MARGIN_PIXEL

    def update_paint_area(self):
        wnd_size = self.size()
        self.__width = wnd_size.width()
        self.__height = wnd_size.height()
        self.__paint_area.setRect(0, 0, self.__width, self.__width)

        self.__axis_width = self.__height if self.__layout == LAYOUT_HORIZON else self.__width
        self.__axis_length = self.__width if self.__layout == LAYOUT_HORIZON else self.__height
        self.__axis_length -= self.DEFAULT_MARGIN_PIXEL * 2

    def update_pixel_per_scale(self):
        self.__pixel_per_scale = self.__axis_length / self.__scale_per_page
        self.__pixel_per_scale = max(self.__pixel_per_scale, TimeAxis.MAIN_SCALE_MIN_PIXEL)

    def calc_paint_parameters(self):
        self.__total_pixel_offset = self.__scroll + self.__offset
        self.__total_tick_offset = self.__total_pixel_offset / self.__pixel_per_scale * self.__main_step

        self.__paint_since_scale = float(self.__total_pixel_offset) / self.__pixel_per_scale
        self.__paint_until_scale = float(self.__total_pixel_offset + self.__axis_length) / self.__pixel_per_scale

        self.__paint_start_scale = math.floor(self.__paint_since_scale)
        self.__paint_start_tick = self.__paint_start_scale * self.__main_step

        axis_metrics = AxisMetrics()
        axis_metrics.set_scale_range(self.__paint_since_scale, self.__paint_until_scale)

    def calc_paint_layout(self):
        # Reserve the text width (hori) / height (vert) of datetime
        era_text_width = 30 if self.__layout == LAYOUT_HORIZON else 80

        left_thread_count = len(self.__left_history_threads)
        right_thread_count = len(self.__right_history_threads)
        self.__axis_mid = int(self.__axis_width * self.__axis_align_offset)

        # TODO: Use AxisMetrics

        self.__axis_left = int(self.__axis_mid - self.__axis_space_w / 2 - 10) - era_text_width
        self.__axis_right = int(self.__axis_mid + self.__axis_space_w / 2 + 10)

        if self.__layout == LAYOUT_HORIZON:
            self.__axis_left = self.__axis_width - self.__axis_left
            self.__axis_right = self.__axis_width - self.__axis_right

            left_thread_width = ((self.__axis_width - self.__axis_left) / left_thread_count) if \
                left_thread_count > 0 else 0
            right_thread_width = (self.__axis_right / right_thread_count) \
                if right_thread_count > 0 else 0
        else:
            left_thread_width = self.__axis_left / left_thread_count if left_thread_count > 0 else 0
            right_thread_width = (self.__axis_width - self.__axis_right) / right_thread_count \
                if right_thread_count > 0 else 0

        # Vertical -> Horizon : Left rotate

        for i in range(0, left_thread_count):
            thread = self.__left_history_threads[i]

            metrics = AxisMetrics()
            metrics.set_align(ALIGN_LEFT)
            metrics.set_layout(self.__layout)

            top = TimeAxis.DEFAULT_MARGIN_PIXEL
            bottom = self.__axis_length - TimeAxis.DEFAULT_MARGIN_PIXEL
            if self.__layout == LAYOUT_HORIZON:
                # TODO: Can we just rotate the QPaint axis?
                left = self.__axis_width - i * left_thread_width
                right = left - left_thread_width
            else:
                left = i * left_thread_width
                right = left + left_thread_width

            metrics.set_transverse_limit(left, right)
            metrics.set_longitudinal_range(top, bottom)
            metrics.set_scale_range(self.__paint_since_scale * self.__main_step,
                                    self.__paint_until_scale * self.__main_step)
            thread.set_thread_metrics(metrics)
            thread.refresh()

            # area = QRect(QPoint(left, top), QPoint(left + left_thread_width, bottom))
            # thread.on_paint_canvas_size_update(area)

        for i in range(0, right_thread_count):
            thread = self.__right_history_threads[i]

            metrics = AxisMetrics()
            metrics.set_align(ALIGN_RIGHT)
            metrics.set_layout(self.__layout)

            top = TimeAxis.DEFAULT_MARGIN_PIXEL
            bottom = self.__axis_length - TimeAxis.DEFAULT_MARGIN_PIXEL
            if self.__layout == LAYOUT_HORIZON:
                # TODO: Can we just rotate the QPaint axis?
                left = self.__axis_right - i * right_thread_width
                right = left - right_thread_width
            else:
                left = self.__axis_right + i * right_thread_width
                right = left + right_thread_width
            metrics.set_transverse_limit(left, right)
            metrics.set_longitudinal_range(top, bottom)
            metrics.set_scale_range(self.__paint_since_scale * self.__main_step,
                                    self.__paint_until_scale * self.__main_step)
            thread.set_thread_metrics(metrics)
            thread.refresh()

            # area = QRect(QPoint(left, top), QPoint(left + right_thread_width, bottom))
            # thread.on_paint_canvas_size_update(area)

    # ----------------------------------------------------- Scale ------------------------------------------------------

    def value_to_pixel(self, value: int, from_origin: bool = False) -> float:
        return float(value - self.__total_tick_offset) / self.__main_step * self.__pixel_per_scale \
               if not from_origin else value / self.__main_step * self.__pixel_per_scale

    def pixel_to_value(self, pixel: int) -> float:
        if pixel in self.__optimise_pixel.keys():
            return self.__optimise_pixel[pixel]
        else:
            return float(pixel) / self.__pixel_per_scale * self.__main_step + self.__total_tick_offset

    # def pixel_offset_to_scale_value(self, display_pixel_offset: int) -> float:
    #     total_pixel_offset = self.__scroll + self.__offset + display_pixel_offset - self.DEFAULT_MARGIN_PIXEL
    #     return total_pixel_offset / self.__pixel_per_scale * self.__main_step

        # delta_pixel_offset = display_pixel_offset + self.__paint_start_offset - self.DEFAULT_MARGIN_PIXEL
        # delta_scale_offset = delta_pixel_offset / self.__pixel_per_scale
        # return (self.__paint_start_scale + delta_scale_offset) * self.__main_step

    def auto_scale(self, since: HistoryTime.TICK, until: HistoryTime.TICK):
        # since_rough = lower_rough(since)
        # until_rough = upper_rough(until)
        # delta = until_rough - since_rough
        # delta_rough = upper_rough(delta)
        step_rough = abs(until - since) / 10

        step_index = 1
        while step_index < len(TimeAxis.STEP_LIST):
            if TimeAxis.STEP_LIST[step_index] < step_rough:
                break
            step_index += 1
        self.select_step_scale(step_index - 1)

        self.update_pixel_per_scale()
        self.__scroll = since * self.__pixel_per_scale

    def select_step_scale(self, step_index: int):
        self.__step_selection = step_index
        self.__step_selection = max(self.__step_selection, 0)
        self.__step_selection = min(self.__step_selection, len(TimeAxis.STEP_LIST) - 1)

        self.__main_step = TimeAxis.STEP_LIST[self.__step_selection]
        self.__sub_step_count = TimeAxis.SUB_STEP_COUNT[self.__step_selection]

        # abs_num = abs(num)
        # if abs_num >= 100:
        #     index_10 = math.log(abs_num, 10)
        #     round_index_10 = math.floor(index_10)
        #     scale = math.pow(10, round_index_10)
        #     delta = scale / 10
        # elif 10 < abs_num < 100:
        #     delta = 10
        # elif 1 < abs_num <= 10:
        #     delta = 1
        # else:
        #     if sign > 0:
        #         delta = 1
        #     else:
        #         delta = 0
        # return sign * delta * ratio

    # ------------------------------------------ Art ------------------------------------------

    def format_real_time_tip(self) -> str:
        # Show The Time From Mouse Position
        tip_text = '(' + str(HistoryTime.year_of_tick(self.__mouse_on_scale_value)) + ')'

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
            if self.__layout == LAYOUT_HORIZON:
                self.__mouse_on_scale_value = self.pixel_to_value(pos.x())
            else:
                self.__mouse_on_scale_value = self.pixel_to_value(pos.y())
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
    thread = TimeThreadBase()
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










