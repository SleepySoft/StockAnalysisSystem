import sys
import traceback
from PyQt5.QtWidgets import QApplication, QScrollBar, QSlider, QMenu

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QStyledItemDelegate, QTreeWidgetItem, QComboBox, QInputDialog, QFileDialog

from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidget, QHBoxLayout, QTableWidgetItem, \
    QWidget, QPushButton, QDockWidget, QLineEdit, QAction, qApp, QMessageBox, QDialog, QVBoxLayout, QLabel, QTextEdit, \
    QListWidget, QShortcut

from .core import *
from .editor import *
from .filter import *
from .indexer import *
from .viewer_ex import *
from .Utility.ui_utility import *


# --------------------------------------------------- Thread Editor ----------------------------------------------------

class ThreadEditor(QWidget):
    def __init__(self, parent=None):
        super(ThreadEditor, self).__init__(parent)

        # Agent Interface:
        #   on_remove(editor: ThreadEditor)
        self.__agent = None

        self.__layout = QVBoxLayout()
        self.__line_width = QLineEdit()
        self.__line_index = QLineEdit()
        self.__radio_left = QRadioButton('Left')
        self.__radio_right = QRadioButton('Right')
        self.__button_browse = QPushButton('Browse')
        self.__button_remove = QPushButton('Remove')

        self.__init_ui()
        self.__config_ui()

    def __init_ui(self):
        self.__layout.addLayout(horizon_layout([QLabel('Thread Index : '), self.__line_index, self.__button_browse]))
        self.__layout.addLayout(horizon_layout([QLabel('Thread Layout: '), self.__radio_left, self.__radio_right,
                                               QLabel('Track Width'), self.__line_width, self.__button_remove]))
        self.setLayout(self.__layout)

    def __config_ui(self):
        self.__line_width.setText('50')
        self.__radio_right.setChecked(True)
        self.__button_browse.clicked.connect(self.on_button_browse)
        self.__button_remove.clicked.connect(self.on_button_remove)

    def set_agent(self, agent):
        self.__agent = agent

    def get_thread_config(self):
        layout = ALIGN_LEFT if self.__radio_left.isChecked() else ALIGN_RIGHT
        try:
            track_width = int(self.__line_width.text())
            track_width = max(10, track_width)
            track_width = min(100, track_width)
        except Exception as e:
            track_width = 50
        finally:
            pass
        track_index = self.__line_index.text()
        return layout, track_width, track_index

    def on_button_browse(self):
        file_choose, filetype = QFileDialog.getOpenFileName(self,
                                                            'Load Filter',
                                                            HistoricalRecordLoader.get_local_depot_root(),
                                                            'Filter Files (*.index)')
        if file_choose != '':
            self.__line_index.setText(file_choose)

    def on_button_remove(self):
        self.__agent.on_thread_remove(self)


# -------------------------------------------------- AppearanceEditor --------------------------------------------------

class AppearanceEditor(QWidget):
    def __init__(self, parent: QWidget = None):
        super(AppearanceEditor, self).__init__(parent)

        self.__thread_editor = []

        self.__radio_horizon = QRadioButton('Horizon')
        self.__radio_vertical = QRadioButton('Vertical')

        self.__label_position = QLabel('50')
        self.__slider_position = QSlider(Qt.Horizontal)
        self.__slider_position.setMinimum(0)
        self.__slider_position.setMaximum(100)
        self.__slider_position.setSliderPosition(50)

        self.__group_thread_editor = None
        self.__layout_thread_editor = None
        self.__button_thread_add = QPushButton('Add')

        self.__thread_place_holder_widget = QWidget()
        self.__thread_place_holder_layout = QHBoxLayout()
        self.__thread_place_holder_widget.setLayout(self.__thread_place_holder_layout)

        self.resize(600, 400)

        self.__init_ui()
        self.__config_ui()

    def __init_ui(self):
        self.__thread_place_holder_layout.addWidget(QLabel(''), 100)
        self.__thread_place_holder_layout.addWidget(self.__button_thread_add, 0)

        group_appearance, layout_appearance = create_v_group_box('Appearance')
        layout_appearance.addLayout(horizon_layout([QLabel('Layout  '), self.__radio_horizon, self.__radio_vertical]))
        layout_appearance.addLayout(horizon_layout([QLabel('Position'), self.__slider_position, self.__label_position]))

        # self.__group_thread_editor, self.__layout_thread_editor = create_v_group_box('Thread Config')
        # self.__layout_thread_editor.addWidget(self.__thread_place_holder_widget)

        # --------------------- Main layout ---------------------
        main_layout = QVBoxLayout()
        main_layout.addWidget(group_appearance)
        main_layout.addWidget(self.__group_thread_editor)
        self.setLayout(main_layout)

    def __config_ui(self):
        self.__radio_vertical.setChecked(True)
        # self.__radio_horizon.setEnabled(False)
        self.__button_thread_add.clicked.connect(self.append_thread)
        self.__slider_position.valueChanged.connect(self.__on_slider_value_changed)

    # ------------------------------------------------------------------------------------------------

    def set_appearance_config(self, config: dict):
        layout = config.get('layout', LAYOUT_VERTICAL)
        offset = config.get('offset', 0.5)
        if layout == LAYOUT_HORIZON:
            self.__radio_horizon.setChecked(True)
        if layout == LAYOUT_VERTICAL:
            self.__radio_vertical.setChecked(True)
        self.__slider_position.setValue(int(100 * offset))
        self.__label_position.setText(str(int(100 * offset)))

    def get_appearance_config(self) -> dict:
        layout = LAYOUT_HORIZON if self.__radio_horizon.isChecked() else LAYOUT_VERTICAL
        offset = float(self.__label_position.text()) / 100
        thread = [thread.get_thread_config() for thread in self.__thread_editor]
        return {
            'layout': layout,
            'offset': offset,
            'thread': thread,
        }

    # ------------------------------------------------------------------------------------------------

    # Interface of ThreadEditor agent
    def on_thread_remove(self, thread: ThreadEditor):
        self.remove_thread(thread)

    def __on_slider_value_changed(self):
        value = self.__slider_position.value()
        self.__label_position.setText(str(value))

    # ------------------------------------------------------------------------------------------------

    def remove_thread(self, thread: ThreadEditor):
        self.__thread_editor.remove(thread)
        thread.setParent(None)
        self.layout_thread_editor()

    def append_thread(self):
        thread = ThreadEditor(self)
        self.__thread_editor.append(thread)
        thread.set_agent(self)
        self.layout_thread_editor()

    def layout_thread_editor(self):
        for i in range(self.__layout_thread_editor.count()):
            layout_item = self.__layout_thread_editor.itemAt(i)
            self.__layout_thread_editor.removeItem(layout_item)
        for thread in self.__thread_editor:
            self.__layout_thread_editor.addWidget(thread)
        self.__layout_thread_editor.addWidget(self.__thread_place_holder_widget)


# ----------------------------------------------------- HistoryUi ------------------------------------------------------

class HistoryUi(QMainWindow):

    def __init__(self):
        super(HistoryUi, self).__init__()

        self.__history = History()
        self.__thread_color_selection = 0

        self.__menu_file = None
        self.__menu_view = None
        self.__menu_help = None

        self.__time_axis = TimeAxis()
        self.__time_axis.set_agent(self)
        self.__time_axis.set_history_core(self.__history)

        self.__init_ui()
        self.__init_menu()

    # ----------------------------- Setup and UI -----------------------------

    def __init_ui(self):
        self.setWindowTitle('SleepySoft/History - Sleepy')
        self.statusBar().showMessage('Ready')
        self.setCentralWidget(self.__time_axis)
        # self.showFullScreen()
        self.resize(1280, 800)
        self.move(QApplication.desktop().screen().rect().center() - self.rect().center())

    def __init_menu(self):
        menu_bar = self.menuBar()

        self.__menu_file = menu_bar.addMenu('File')
        self.__menu_view = menu_bar.addMenu('View')
        self.__menu_help = menu_bar.addMenu('Help')

        # ----------------------- File -----------------------

        file_action = QAction('&Load Files', self)
        file_action.setShortcut('Ctrl+F')
        file_action.setStatusTip('Load a .his file')
        file_action.triggered.connect(self.on_menu_load_files)
        self.__menu_file.addAction(file_action)

        depot_action = QAction('&Load Depot', self)
        depot_action.setShortcut('Ctrl+D')
        depot_action.setStatusTip('Load a depot')
        depot_action.triggered.connect(self.on_menu_load_depot)
        self.__menu_file.addAction(depot_action)

        load_all_action = QAction('&Load All Records', self)
        load_all_action.setShortcut('Ctrl+A')
        load_all_action.setStatusTip('Load all depot')
        load_all_action.triggered.connect(self.on_menu_load_all)
        self.__menu_file.addAction(load_all_action)

        exit_action = QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit app')
        exit_action.triggered.connect(qApp.quit)
        self.__menu_file.addAction(exit_action)

        # ----------------------- View -----------------------

        action = QAction('&Historical Record Editor', self)
        action.setShortcut('Ctrl+R')
        action.setStatusTip('Open Historical Record Editor')
        action.triggered.connect(self.on_menu_record_editor)
        self.__menu_view.addAction(action)

        action = QAction('&History Filter Editor', self)
        action.setShortcut('Ctrl+R')
        action.setStatusTip('Open History Filter Editor')
        action.triggered.connect(self.on_menu_filter_editor)
        self.__menu_view.addAction(action)

        action = QAction('&Axis Appearance Setting', self)
        action.setShortcut('Ctrl+T')
        action.setStatusTip('Open Axis Appearance Setting')
        action.triggered.connect(self.on_menu_thread_editor)
        self.__menu_view.addAction(action)

        # ----------------------- Help -----------------------

        help_action = QAction('&Help', self)
        help_action.setShortcut('Ctrl+H')
        help_action.setStatusTip('Open help Window')
        help_action.triggered.connect(self.on_menu_help)
        self.__menu_help.addAction(help_action)

        about_action = QAction('&About', self)
        about_action.setShortcut('Ctrl+B')
        about_action.setStatusTip('Open about Window')
        about_action.triggered.connect(self.on_menu_about)
        self.__menu_help.addAction(about_action)

        # ------------------ Right Button Menu ------------------

        self.__time_axis.setContextMenuPolicy(Qt.CustomContextMenu)
        self.__time_axis.customContextMenuRequested.connect(self.on_custom_menu)

    # ----------------------------- UI Events -----------------------------

    def on_menu_load_files(self):
        root_path = HistoricalRecordLoader.get_local_depot_root()
        fname, ftype = QFileDialog.getOpenFileNames(self,
                                                    'Select History Files',
                                                    root_path,
                                                    'History Files (*.his)')
        sources = [f[len(root_path):] if f.startswith(root_path) else f for f in fname]
        for source in sources:
            self.__history.load_source(source)

    def on_menu_load_depot(self):
        pass

    def on_menu_load_all(self):
        depots = HistoryRecordBrowser.enumerate_local_depot()
        for depot in depots:
            self.__history.load_depot(depot)

    def on_menu_record_editor(self):
        editor = HistoryEditorDialog()
        editor.exec()

    def on_menu_filter_editor(self):
        wnd = FilterEditor()
        dlg = WrapperQDialog(wnd)
        dlg.exec()

    def on_menu_thread_editor(self):
        wnd = AppearanceEditor()
        wnd.set_appearance_config(self.load_appearance_config())

        dlg = WrapperQDialog(wnd, True)
        dlg.exec()
        if dlg.is_ok():
            self.apply_appearance_config(wnd.get_appearance_config())

    def on_menu_help(self):
        try:
            pass
            # import readme
            # help_wnd = InfoDialog('Help', readme.TEXT)
            # help_wnd.exec()
        except Exception as e:
            pass
        finally:
            pass

    def on_menu_about(self):
        try:
            pass
            # import readme
            # QMessageBox.about(self, 'About', readme.ABOUT)
        except Exception as e:
            pass
        finally:
            pass

    def on_menu_selected(self, docker):
        if docker is not None:
            if docker.isVisible():
                docker.hide()
            else:
                docker.show()

    # ------------------------------ Right Click Menu ------------------------------

    def on_custom_menu(self, pos: QPoint):
        align = self.__time_axis.align_from_point(pos)
        thread = self.__time_axis.thread_from_point(pos)

        opt_load_file = None
        opt_load_index = None
        opt_open_filter = None
        opt_add_thread = None
        opt_add_thread_left = None
        opt_add_thread_right = None
        opt_remove_thread = None
        opt_set_track_width = None

        menu = QMenu()
        if thread is None:
            opt_add_thread = menu.addAction("Add Thread")
        else:
            opt_load_index = menu.addAction("Load Index")
            opt_load_file = menu.addAction("Load File")
            opt_open_filter = menu.addAction("Use Filter")
            opt_set_track_width = menu.addAction("Set Track Width")
            opt_remove_thread = menu.addAction("Remove Thread")
            opt_add_thread_left = menu.addAction("Add Thread On Left")
            opt_add_thread_right = menu.addAction("Add Thread On Right")

        action = menu.exec_(self.__time_axis.mapToGlobal(pos))
        if action is None:
            return

        # --------------------------- Add ---------------------------

        if action == opt_add_thread or \
                action == opt_add_thread_left or \
                action == opt_add_thread_right:
            if action == opt_add_thread_left:
                align = ALIGN_LEFT
            elif action == opt_add_thread_right:
                align = ALIGN_RIGHT
            new_thread = HistoryIndexTrack()
            self.__thread_color_selection += 1
            new_thread.set_thread_color(THREAD_BACKGROUND_COLORS[self.__thread_color_selection %
                                                                 len(THREAD_BACKGROUND_COLORS)])
            new_thread.set_thread_event_indexes([])
            new_thread.set_thread_min_track_width(HistoryIndexTrack.REFERENCE_TRACK_WIDTH)
            self.__time_axis.add_history_thread(new_thread, align, thread)

        # --------------------------- Remove ---------------------------

        elif action == opt_remove_thread:
            self.__time_axis.remove_history_thread(thread)

        # --------------------------- Config ---------------------------

        elif action == opt_set_track_width:
            width, ok = QInputDialog.getInt(self, 'Input Track Width', 'Track Width', value=50)
            if ok:
                thread.set_thread_min_track_width(width)

        # --------------------------- Loads ---------------------------

        elif action == opt_load_index:
            file_choose, file_type = QFileDialog.getOpenFileName(self, 'Load Index',
                                                                 HistoricalRecordLoader.get_local_depot_root(),
                                                                 'Filter Files (*.index)')
            if file_choose != '':
                indexer = HistoricalRecordIndexer()
                indexer.load_from_file(file_choose)
                thread.set_thread_event_indexes(indexer.get_indexes())

        elif action == opt_load_file:
            file_choose, file_type = QFileDialog.getOpenFileName(self, 'Load Filter',
                                                                 HistoricalRecordLoader.get_local_depot_root(),
                                                                 'Filter Files (*.his)')
            if file_choose != '':
                records = self.__history.load_source(file_choose)
                thread.set_thread_event_indexes([record.to_index() for record in records])

        elif action == opt_open_filter:
            wnd = FilterEditor()
            wnd.set_history_core(self.__history)
            dlg = WrapperQDialog(wnd, True)
            dlg.exec()
            if dlg.is_ok():
                his_filter = wnd.ui_to_filter()
                records = self.__history.select_records(
                    sources=his_filter.get_sources(),
                    focus_label=his_filter.get_focus_label(),
                    include_label_tags=his_filter.get_include_tags(), include_all=False,
                    exclude_label_tags=his_filter.get_exclude_tags(), exclude_any=True)
                thread.set_thread_event_indexes([record.to_index() for record in records])

        else:
            return

    def closeEvent(self, event):
        """Generate 'question' dialog on clicking 'X' button in title bar.
        Reimplement the closeEvent() event handler to include a 'Question'
        dialog with options on how to proceed - Save, Close, Cancel buttons
        """
        reply = QMessageBox.question(self,
                                     QtCore.QCoreApplication.translate('main', '退出?'),
                                     QtCore.QCoreApplication.translate('main', '是否确认退出？'),
                                     QMessageBox.Close | QMessageBox.Cancel,
                                     QMessageBox.Cancel)
        if reply == QMessageBox.Close:
            event.accept()
        else:
            event.ignore()

    # ------------------------------------------------------------------------------------------------------------------

    def load_appearance_config(self) -> dict:
        return {
            'layout': self.__time_axis.get_axis_layout(),
            'offset': self.__time_axis.get_axis_offset(),
        }

    def apply_appearance_config(self, config: dict):
        if 'layout' in config.keys():
            self.__time_axis.set_axis_layout(config.get('layout'))
        if 'offset' in config.keys():
            self.__time_axis.set_axis_offset(config.get('offset'))

        # self.__time_axis.remove_all_history_threads()

        # thread_index = 0
        # for align, track_width, track_index in thread_config:
        #     indexer = HistoricalRecordIndexer()
        #     indexer.load_from_file(track_index)
        #
        #     thread = HistoryIndexTrack()
        #     thread.set_thread_color(THREAD_BACKGROUND_COLORS[thread_index])
        #     thread.set_thread_event_indexes(indexer.get_indexes())
        #     thread.set_thread_min_track_width(track_width)
        #     # thread.set_thread_align(align)
        #     # thread.set_thread_layout(layout)
        #     self.__time_axis.add_history_thread(thread, align)
        #
        #     thread_index += 1


# ----------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    main_wnd = HistoryUi()
    main_wnd.show()
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
