#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import pandas as pd
from functools import partial
from types import SimpleNamespace

from PyQt5 import QtCore
from PyQt5.QtGui import QFont, QStandardItemModel, QStandardItem
from PyQt5.QtCore import pyqtSignal, Qt, QAbstractTableModel, QModelIndex, QRect, QVariant, QSize
from PyQt5.QtWidgets import QMainWindow, QApplication, QHBoxLayout, QWidget, QPushButton, \
    QDockWidget, QAction, qApp, QMessageBox, QDialog, QVBoxLayout, QLabel, QGroupBox, QTableWidget, \
    QTableWidgetItem, QTabWidget, QLayout, QTextEdit, QListWidget, QListWidgetItem, QMenu, QHeaderView, \
    QStyle, QStyleOptionButton, QTableView


# ----------------------------------------------------------------------------------------------------------------------

def horizon_layout(widgets: list, weights: list = None) -> QHBoxLayout:
    layout = QHBoxLayout()
    if weights is None:
        weights = []
    while len(weights) < len(widgets):
        weights.append(1)
    for widget, weight in zip(widgets, weights):
        layout.addWidget(widget, weight)
    return layout


def create_v_group_box(title: str) -> (QGroupBox, QVBoxLayout):
    group_box = QGroupBox(title)
    group_layout = QVBoxLayout()
    # group_layout.addStretch(1)
    group_box.setLayout(group_layout)
    return group_box, group_layout


def create_h_group_box(title: str) -> (QGroupBox, QHBoxLayout):
    group_box = QGroupBox(title)
    group_layout = QHBoxLayout()
    # group_layout.addStretch(1)
    group_box.setLayout(group_layout)
    return group_box, group_layout


def create_new_tab(tab_widget: QTabWidget, title: str, layout: QLayout = None) -> QLayout:
    empty_wnd = QWidget()
    wnd_layout = layout if layout is not None else QVBoxLayout()
    empty_wnd.setLayout(wnd_layout)
    tab_widget.addTab(empty_wnd, title)
    return wnd_layout


def restore_text_editor(editor: QTextEdit):
    editor.clear()
    editor.setFocus()
    font = QFont()
    font.setFamily("微软雅黑")
    font.setPointSize(10)
    editor.selectAll()
    editor.setCurrentFont(font)
    editor.setTextColor(Qt.black)
    editor.setTextBackgroundColor(Qt.white)


# Takes a df and writes it to a qtable provided. df headers become qtable headers
# From: https://stackoverflow.com/a/57225144

def write_df_to_qtable(df: pd.DataFrame, table: QTableWidget):
    headers = list(df)
    table.setRowCount(df.shape[0])
    table.setColumnCount(df.shape[1])
    table.setHorizontalHeaderLabels(headers)

    # getting data from df is computationally costly so convert it to array first
    df_array = df.values
    for row in range(df.shape[0]):
        for col in range(df.shape[1]):
            table.setItem(row, col, QTableWidgetItem(str(df_array[row, col])))


# ----------------------------------------------------------------------------------------------------------------------
#                                                   InfoDialog
# ----------------------------------------------------------------------------------------------------------------------

class InfoDialog(QDialog):
    def __init__(self, title, text):
        super().__init__()
        self.__text = text
        self.__title = title
        self.__button_ok = QPushButton('OK')
        self.__layout_main = QVBoxLayout()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.__title)
        self.__button_ok.clicked.connect(self.on_btn_click_ok)
        self.__layout_main.addWidget(QLabel(self.__text), 1)
        self.__layout_main.addWidget(self.__button_ok)
        self.setLayout(self.__layout_main)

    def on_btn_click_ok(self):
        self.close()


# ----------------------------------------------------------------------------------------------------------------------
#                                                   DataFrameWidget
# ----------------------------------------------------------------------------------------------------------------------

class DataFrameWidget(QWidget):
    def __init__(self, df: pd.DataFrame = None):
        super(DataFrameWidget, self).__init__()

        self.__data_frame = df
        self.__table_main = EasyQTableWidget()

        self.init_ui()
        self.update_table(df)

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.__table_main)
        self.setLayout(main_layout)

    def __config_control(self):
        self.setMinimumSize(QSize(1000, 700))

    def update_table(self, df: pd.DataFrame):
        if df is not None:
            self.__data_frame = df
            write_df_to_qtable(self.__data_frame, self.__table_main)


# ----------------------------------------------------------------------------------------------------------------------
#                                                   CommonMainWindow
# ----------------------------------------------------------------------------------------------------------------------

class CommonMainWindow(QMainWindow):

    def __init__(self, hold_menu: bool = False):
        super(CommonMainWindow, self).__init__()
        self.menu_file = None
        self.menu_view = None
        self.menu_help = None

        self.__hold_menu = False
        self.__sub_window_table = {}
        
        self.common_init_ui()
        self.common_init_menu()
        # self.init_sub_window()

    # ----------------------------- Setup and UI -----------------------------

    def common_init_ui(self):
        self.setWindowTitle('Common Main Window - Sleepy')
        self.statusBar().showMessage('Ready')
        # self.showFullScreen()
        self.resize(1280, 800)
        self.setDockNestingEnabled(True)
        self.move(QApplication.desktop().screen().rect().center() - self.rect().center())

    def common_init_menu(self):
        menu_bar = self.menuBar()

        if not self.__hold_menu:
            self.menu_file = menu_bar.addMenu('File')
            self.menu_view = menu_bar.addMenu('View')
            self.menu_help = menu_bar.addMenu('Help')
        else:
            self.menu_file = QMenu('File')
            self.menu_view = QMenu('View')
            self.menu_help = QMenu('Help')

        exit_action = QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit app')
        exit_action.triggered.connect(qApp.quit)
        self.menu_file.addAction(exit_action)

        help_action = QAction('&Help', self)
        help_action.setShortcut('Ctrl+H')
        help_action.setStatusTip('Open help Window')
        help_action.triggered.connect(self.on_menu_help)
        self.menu_help.addAction(help_action)

        about_action = QAction('&About', self)
        about_action.setStatusTip('Open about Window')
        about_action.triggered.connect(self.on_menu_about)
        self.menu_help.addAction(about_action)

    # def init_sub_window(self):
        # self.__add_sub_window(self.__serial_port_module, {
        #     'DockName': self.__translate('main', ''),
        #     'DockArea': Qt.RightDockWidgetArea,
        #     'DockShow': True,
        #     'DockFloat': False,
        #     'MenuPresent': True,
        #     'ActionTips': self.__translate('main', ''),
        #     'ActionShortcut': 'Ctrl+S',
        # })

    def get_sub_window(self, name: str) -> SimpleNamespace or None:
        return self.__sub_window_table.get(name, None)

    def add_sub_window(self, window: QWidget, name: str, config: dict, menu: QMenu = None):
        sub_window_data = SimpleNamespace()
        sub_window_data.config = config
        self.__setup_sub_window_dock(window, config, sub_window_data)
        self.__setup_sub_window_menu(config, sub_window_data, menu)
        self.__setup_sub_window_action(config, sub_window_data)
        self.__sub_window_table[name] = sub_window_data

    def __setup_sub_window_dock(self, window: QWidget, config: dict, sub_window_data: SimpleNamespace):
        dock_name = config.get('DockName', '')
        dock_area = config.get('DockArea', Qt.NoDockWidgetArea)
        dock_show = config.get('DockShow', False)
        dock_float = config.get('DockFloat', False)

        dock_wnd = QDockWidget(dock_name, self)
        dock_wnd.setAllowedAreas(
            Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea | Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
        # With this setting, the dock widget cannot be closed
        # dock_wnd.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        if dock_area != Qt.NoDockWidgetArea:
            if dock_area == Qt.AllDockWidgetAreas:
                self.addDockWidget(Qt.TopDockWidgetArea, dock_wnd)
                dock_wnd.setFloating(True)
                dock_wnd.move(QApplication.desktop().screen().rect().center() - self.rect().center())
            else:
                self.addDockWidget(dock_area, dock_wnd)
        else:
            self.addDockWidget(Qt.TopDockWidgetArea, dock_wnd)
            dock_wnd.setFloating(True)
            dock_wnd.setAllowedAreas(Qt.NoDockWidgetArea)
            dock_wnd.move(QApplication.desktop().screen().rect().center() - self.rect().center())

        dock_wnd.setWidget(window)
        if dock_float:
            dock_wnd.setFloating(True)
            # self.geometry().center() - dock_wnd.rect().center()
            # dock_wnd.move()
        if dock_show:
            dock_wnd.show()
        else:
            dock_wnd.hide()
        sub_window_data.dock_wnd = dock_wnd

    def __setup_sub_window_menu(self, config: dict, sub_window_data: SimpleNamespace, menu: QMenu):
        menu_present = config.get('MenuPresent', False)
        dock_wnd = sub_window_data.dock_wnd if hasattr(sub_window_data, 'dock_wnd') else None

        if menu_present and dock_wnd is not None:
            menu_view = self.menu_view if menu is None else menu
            menu_view.addAction(dock_wnd.toggleViewAction())

    def __setup_sub_window_action(self, config: dict, sub_window_data: SimpleNamespace):
        action_tips = config.get('ActionTips', '')
        action_shortcut = config.get('ActionShortcut', '')
        menu_action = sub_window_data.menu_action if hasattr(sub_window_data, 'menu_action') else None

        if menu_action is not None:
            if action_shortcut != '':
                menu_action.setShortcut(action_shortcut)
            menu_action.setStatusTip(action_tips)

    # ----------------------------- UI Events -----------------------------

    def on_menu_help(self):
        try:
            import readme
            help_wnd = InfoDialog('Help', readme.TEXT)
            help_wnd.exec()
        except Exception as e:
            pass
        finally:
            pass

    def on_menu_about(self):
        try:
            import readme
            QMessageBox.about(self, 'About', readme.ABOUT + 'Version: ' + readme.VERSION)
        except Exception as e:
            pass
        finally:
            pass

    def closeEvent(self, event):
        reply = QMessageBox.question(self,
                                     QtCore.QCoreApplication.translate('main', 'Quit'),
                                     QtCore.QCoreApplication.translate('main', 'Are you sure to quit'),
                                     QMessageBox.Yes | QMessageBox.Cancel,
                                     QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            event.accept()
            QApplication.quit()
        else:
            event.ignore()


# ----------------------------------------------------------------------------------------------------------------------
#                                                   WrapperQDialog
# ----------------------------------------------------------------------------------------------------------------------

class WrapperQDialog(QDialog):
    """
    Wrap a QWidget in a QDialog which has 'OK' and 'Cancel' button as default
    :param wrapped_wnd: The Widget you want to warp
    :param has_button: Show 'OK' and 'Cancel' button or not.
    """
    def __init__(self, wrapped_wnd: QWidget, has_button: bool = False):
        super(WrapperQDialog, self).__init__()

        self.__is_ok = False
        self.__wrapped_wnd_destroyed = False

        self.__wrapped_wnd = wrapped_wnd
        self.__wrapped_wnd.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.__wrapped_wnd.destroyed.connect(self.on_wrap_wnd_destroyed)
        self.__has_button = has_button

        self.__button_ok = QPushButton('OK')
        self.__button_cancel = QPushButton('Cancel')

        layout = QVBoxLayout()
        layout.addWidget(self.__wrapped_wnd)

        self.setWindowTitle(self.__wrapped_wnd.windowTitle())

        if has_button:
            line = QHBoxLayout()
            line.addWidget(QLabel(), 100)
            line.addWidget(self.__button_ok, 0)
            line.addWidget(self.__button_cancel, 0)
            self.__button_ok.clicked.connect(self.on_button_ok)
            self.__button_cancel.clicked.connect(self.on_button_cancel)
            layout.addLayout(line)

        self.setLayout(layout)
        self.setWindowFlags(int(self.windowFlags()) |
                            Qt.WindowMinMaxButtonsHint |
                            QtCore.Qt.WindowSystemMenuHint)

    def is_ok(self):
        """
        Check whether user clicking the 'OK' button.
        :return: True if user close the Dialog by clicking 'OK' button else False
        """
        return self.__is_ok

    def get_wrapped_wnd(self) -> QWidget:
        return self.__wrapped_wnd

    def on_button_ok(self):
        self.__is_ok = True
        self.close()

    def on_button_cancel(self):
        self.close()

    def on_wrap_wnd_destroyed(self):
        self.__wrapped_wnd_destroyed = True
        self.close()

    def closeEvent(self, event):
        if self.__wrapped_wnd_destroyed:
            event.accept()
        else:
            if self.__wrapped_wnd.close():
                event.accept()
            else:
                event.ignore()


# ----------------------------------------------------------------------------------------------------------------------
#                                                   EasyQTableWidget
# ----------------------------------------------------------------------------------------------------------------------

class EasyQTableWidget(QTableWidget):
    """
    QTableWidget assistance class
    """
    def __init__(self, *__args):
        super(EasyQTableWidget, self).__init__(*__args)

    def AppendRow(self, content: [str]):
        row_count = self.rowCount()
        self.insertRow(row_count)
        for col in range(0, len(content)):
            self.setItem(row_count, col, QTableWidgetItem(content[col]))

    def GetCurrentRow(self) -> [str]:
        row_index = self.GetCurrentIndex()
        if row_index == -1:
            return []
        return [self.model().index(row_index, col_index).data() for col_index in range(self.columnCount())]

    def GetCurrentIndex(self) -> int:
        return self.selectionModel().currentIndex().row() if self.selectionModel().hasSelection() else -1

    def AddWidgetToCell(self, row: int, col: int, widgets: [QWidget]):
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        wrap_widget = QWidget()
        wrap_widget.setLayout(layout)
        wrap_widget.setContentsMargins(0, 0, 0, 0)
        if not isinstance(widgets, (list, tuple)):
            widgets = [widgets]
        for widget in widgets:
            layout.addWidget(widget)
        self.setCellWidget(row, col, wrap_widget)


# ----------------------------------------------------------------------------------------------------------------------
#                                                    EasyQListSuite
# ----------------------------------------------------------------------------------------------------------------------

class EasyQListSuite(QWidget):
    """
    Provide a window that has a QListWidget with 'Add' and 'Remove' button.
    """
    def __init__(self, *__args):
        super(EasyQListSuite, self).__init__(*__args)

        self.__item_list = []

        self.__list_main = QListWidget(self)
        self.__button_add = QPushButton('Add')
        self.__button_remove = QPushButton('Remove')

        self.__init_ui()
        self.__config_ui()

    def update_item(self, items: [(str, any)]):
        """
        Specify a (key, value) tuple list.
            Key will be displayed as list item.
            Value can be retrieved by get_select_items()
        :param items: Specify a (key, value) tuple list.
        :return: None
        """
        self.__item_list.clear()
        for item in items:
            if isinstance(item, (list, tuple)):
                if len(item) == 0:
                    continue
                elif len(item) == 1:
                    self.__item_list.append((str(item[0]), item[0]))
                else:
                    self.__item_list.append((str(item[0]), item[1]))
            else:
                self.__item_list.append((str(item), item))
        self.__update_list()

    def get_select_items(self) -> [any]:
        """
        Get the value of the items that user selected.
        :return: The value of the items that user selected.
        """
        return [item.data(Qt.UserRole) for item in self.__list_main.selectedItems()]

    def set_add_handler(self, handler):
        """
        Add a handler for 'Add' button clicking
        :param handler: The handler that connects to the button clicked signal
        :return:
        """
        self.__button_add.clicked.connect(handler)

    def set_remove_handler(self, handler):
        """
        Add a handler for 'Remove' button clicking
        :param handler: The handler that connects to the button clicked signal
        :return:
        """
        self.__button_remove.clicked.connect(handler)

    # ---------------------------------------- Private ----------------------------------------

    def __init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        line_layout = QHBoxLayout()
        line_layout.addWidget(self.__button_add)
        line_layout.addWidget(self.__button_remove)

        main_layout.addWidget(self.__list_main)
        main_layout.addLayout(line_layout)

    def __config_ui(self):
        pass

    def __update_list(self):
        self.__list_main.clear()
        for text, obj in self.__item_list:
            item = QListWidgetItem()
            item.setText(text)
            item.setData(Qt.UserRole, obj)
            self.__list_main.addItem(item)


# --------------------------------------------------- PageTableWidget --------------------------------------------------

class PageTableWidget(QWidget):
    def __init__(self):
        super(PageTableWidget, self).__init__()

        self.__page = 0
        self.__max_page = 0
        self.__item_per_page = 50
        self.__max_item_count = 0

        self.__table_main = EasyQTableWidget()
        self.__layout_bottom = QHBoxLayout()

        self.init_ui()

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(self.__table_main)
        main_layout.addLayout(self.__layout_bottom)

    def __config_control(self):
        self.add_extra_button('<<', '<<')
        self.add_extra_button('<', '<')
        self.add_extra_button('>', '>')
        self.add_extra_button('>>', '>>')

    # ------------------------------------- Function -------------------------------------

    def get_table(self) -> EasyQTableWidget:
        return self.__table_main

    def get_item_offset(self) -> int:
        return self.__page * self.__item_per_page

    def get_item_per_page(self) -> int:
        return self.__item_per_page

    def set_max_item(self, count: int):
        self.__max_item_count = count
        self.__update_max_page()

    def set_item_pre_page(self, count: int):
        if self.__item_per_page != count:
            self.__item_per_page = count
            self.__update_max_page()
            self.on_content_update()

    def add_extra_button(self, caption: str, button_mark: str):
        button = QPushButton(caption)
        self.__layout_bottom.addWidget(button)
        button.clicked.connect(partial(self.on_button_event, button_mark))

    # ---------------------------------- Event Handling ----------------------------------

    def on_button_event(self, control: str):
        if control in ['<<', '<', '>', '>>']:
            self.on_page_control(control)
        else:
            self.on_extra_control(control)

    def on_page_control(self, control: str):
        if control == '<<':
            self.__page = 0
        elif control == '<':
            self.__page = max(self.__page - 1, 0)
        elif control == '>':
            self.__page = min(self.__page + 1, self.__max_page)
        elif control == '>>':
            self.__page = self.__max_page
        self.on_content_update()

    # ------------------------------------- Override -------------------------------------

    def on_extra_control(self, control: str):
        # TODO: Override this function to handle extra button event
        pass

    def on_content_update(self):
        # TODO: Override this function to handle content update
        pass

    def __update_max_page(self):
        self.__max_page = (self.__max_item_count / self.__item_per_page) if self.__item_per_page > 0 else 0
        if self.__page > self.__max_page:
            self.__page = self.__max_page


# ----------------------------------------------------------------------------------------------------------------------
#                                                   DataFrameModel
# ----------------------------------------------------------------------------------------------------------------------

class DataFrameModel(QtCore.QAbstractTableModel):
    """
    From: https://stackoverflow.com/a/44605011
        Use with QTableView.setModel()
    """
    DtypeRole = QtCore.Qt.UserRole + 1000
    ValueRole = QtCore.Qt.UserRole + 1001

    def __init__(self, df=pd.DataFrame(), parent=None):
        super(DataFrameModel, self).__init__(parent)
        self._dataframe = df

    def setDataFrame(self, dataframe):
        self.beginResetModel()
        self._dataframe = dataframe.copy()
        self.endResetModel()

    def dataFrame(self):
        return self._dataframe

    dataFrame = QtCore.pyqtProperty(pd.DataFrame, fget=dataFrame, fset=setDataFrame)

    @QtCore.pyqtSlot(int, QtCore.Qt.Orientation, result=str)
    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._dataframe.columns[section]
            else:
                return str(self._dataframe.index[section])
        return QtCore.QVariant()

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._dataframe.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        return self._dataframe.columns.size

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()
                                       and 0 <= index.column() < self.columnCount()):
            return QtCore.QVariant()
        row = self._dataframe.index[index.row()]
        col = self._dataframe.columns[index.column()]
        dt = self._dataframe[col].dtype

        val = self._dataframe.iloc[row][col]
        if role == QtCore.Qt.DisplayRole:
            return str(val)
        elif role == DataFrameModel.ValueRole:
            return val
        if role == DataFrameself.DtypeRole:
            return dt
        return QtCore.QVariant()

    def roleNames(self):
        roles = {
            QtCore.Qt.DisplayRole: b'display',
            DataFrameModel.DtypeRole: b'dtype',
            DataFrameModel.ValueRole: b'value'
        }
        return roles










