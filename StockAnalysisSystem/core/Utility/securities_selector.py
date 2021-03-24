import sys
import threading
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QTimer, QSortFilterProxyModel, QSize
from PyQt5.QtWidgets import QCompleter, QComboBox, QDialog, QVBoxLayout, QPushButton, QTableWidget, QHBoxLayout, \
    QApplication, QListWidget
from StockAnalysisSystem.core.Utility.common import ThreadSafeSingleton
from StockAnalysisSystem.interface.interface import SasInterface as sasIF


class SecuritiesSelector(QComboBox):
    class SingletonStorage(metaclass=ThreadSafeSingleton):
        def __init__(self):
            self.__stock_list = []
            self.__lock = threading.Lock()
            self.__refresh_thread = None

        def get_stock_list(self) -> list:
            with self.__lock:
                return self.__stock_list.copy()

        def refresh_stock_list(self, sas_if: sasIF):
            with self.__lock:
                if self.__refresh_thread is None:
                    self.__refresh_thread = threading.Thread(target=self.__update_stock_list,
                                                             name='SecuritiesSelectorRefresh',
                                                             args=(sas_if,))
                    self.__refresh_thread.start()

        def __update_stock_list(self, sas_if: sasIF):
            stock_list = sas_if.sas_get_stock_info_list()
            with self.__lock:
                self.__stock_list = stock_list
                self.__refresh_thread = None

    def __init__(self, sas_if: sasIF, parent=None):
        super(SecuritiesSelector, self).__init__(parent)

        self.__sas_if: sasIF = sas_if

        self.__timer = QTimer()
        self.__timer.setInterval(1000)
        self.__timer.timeout.connect(self.on_timer)

        if self.__sas_if is not None:
            # Timer for update stock list
            self.__timer.start()

        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable(True)
        self.addItem('Loading...')

        # add a filter model to filter matching items
        self.pFilterModel = QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())

        # add a completer, which uses the filter model
        self.completer = QCompleter(self.pFilterModel, self)
        # always show all (filtered) completions
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)

        # connect signals
        self.lineEdit().textEdited.connect(self.pFilterModel.setFilterFixedString)
        self.completer.activated.connect(self.on_completer_activated)

    # def keyPressEvent(self, event):
    #     super(SecuritiesSelector, self).keyPressEvent(event)
    #     key = event.key()
    #     if event.key() == QtCore.Qt.Key_Return:
    #         print('return key pressed')
    #     else:
    #         print('key pressed: %i' % key)

    def on_timer(self):
        # Check stock list ready and update combobox
        # if self.__data_utility is not None and \
        #         self.__data_utility.stock_cache_ready():
        #     stock_list = self.__data_utility.get_stock_list()

        stock_list = SecuritiesSelector.SingletonStorage().get_stock_list()
        if len(stock_list) > 0:
            self.clear()
            for stock_identity, stock_name in stock_list:
                self.addItem(stock_identity + ' | ' + stock_name, stock_identity)
            self.__timer.stop()
        else:
            SecuritiesSelector.SingletonStorage().refresh_stock_list(self.__sas_if)

    # on selection of an item from the completer, select the corresponding item from combobox
    def on_completer_activated(self, text: str):
        if self.__data_utility is None or \
                not self.__data_utility.stock_cache_ready():
            return
        if text is not None and text != '':
            self.__data_utility.guess_securities(text)
            index = self.findData(text)
            self.setCurrentIndex(index)
            self.activated[str].emit(self.itemText(index))

    def setModel(self, model):
        super(QComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(QComboBox, self).setModelColumn(column)

    def select_security(self, security: str, linkage: bool):
        for index in range(self.count()):
            stock_identity = self.itemData(index)
            if stock_identity == security:
                self.setCurrentIndex(index)
                break

    def get_input_securities(self) -> str:
        # select_index = self.currentIndex()
        # if select_index >= 0:
        #     return self.itemData(select_index)
        # else:
        input_securities = self.currentText()
        if '|' in input_securities:
            input_securities = input_securities.split('|')[0].strip()
        return input_securities.strip()

    def get_select_securities(self) -> str:
        select_index = self.currentIndex()
        return self.itemData(select_index) if select_index >= 0 else ''


# class SecuritiesSelector(QComboBox):
#     def __init__(self, data_utility: DataUtility, parent=None):
#         super(SecuritiesSelector, self).__init__(parent)
#
#         self.__data_utility: DataUtility = data_utility
#
#         self.__timer = QTimer()
#         self.__timer.setInterval(1000)
#         self.__timer.timeout.connect(self.on_timer)
#
#         if self.__data_utility is not None:
#             # Timer for update stock list
#             self.__timer.start()
#
#         self.setFocusPolicy(Qt.StrongFocus)
#         self.setEditable(True)
#
#         # add a filter model to filter matching items
#         self.pFilterModel = QSortFilterProxyModel(self)
#         self.pFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
#         self.pFilterModel.setSourceModel(self.model())
#
#         # add a completer, which uses the filter model
#         self.completer = QCompleter(self.pFilterModel, self)
#         # always show all (filtered) completions
#         self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
#         self.setCompleter(self.completer)
#
#         # connect signals
#         self.lineEdit().textEdited.connect(self.pFilterModel.setFilterFixedString)
#         self.completer.activated.connect(self.on_completer_activated)
#
#     # def keyPressEvent(self, event):
#     #     super(SecuritiesSelector, self).keyPressEvent(event)
#     #     key = event.key()
#     #     if event.key() == QtCore.Qt.Key_Return:
#     #         print('return key pressed')
#     #     else:
#     #         print('key pressed: %i' % key)
#
#     def on_timer(self):
#         # Check stock list ready and update combobox
#         if self.__data_utility is not None and \
#                 self.__data_utility.stock_cache_ready():
#             stock_list = self.__data_utility.get_stock_list()
#             for stock_identity, stock_name in stock_list:
#                 self.addItem(stock_identity + ' | ' + stock_name, stock_identity)
#             self.__timer.stop()
#
#     # on selection of an item from the completer, select the corresponding item from combobox
#     def on_completer_activated(self, text: str):
#         if self.__data_utility is None or \
#                 not self.__data_utility.stock_cache_ready():
#             return
#         if text is not None and text != '':
#             self.__data_utility.guess_securities(text)
#             index = self.findData(text)
#             self.setCurrentIndex(index)
#             self.activated[str].emit(self.itemText(index))
#
#     def setModel(self, model):
#         super(QComboBox, self).setModel(model)
#         self.pFilterModel.setSourceModel(model)
#         self.completer.setModel(self.pFilterModel)
#
#     def setModelColumn(self, column):
#         self.completer.setCompletionColumn(column)
#         self.pFilterModel.setFilterKeyColumn(column)
#         super(QComboBox, self).setModelColumn(column)
#
#     def select_security(self, security: str, linkage: bool):
#         for index in range(self.count()):
#             stock_identity = self.itemData(index)
#             if stock_identity == security:
#                 self.setCurrentIndex(index)
#                 break
#
#     def get_input_securities(self) -> str:
#         # select_index = self.currentIndex()
#         # if select_index >= 0:
#         #     return self.itemData(select_index)
#         # else:
#         input_securities = self.currentText()
#         if '|' in input_securities:
#             input_securities = input_securities.split('|')[0].strip()
#         return input_securities.strip()
#
#     def get_select_securities(self) -> str:
#         select_index = self.currentIndex()
#         return self.itemData(select_index) if select_index >= 0 else ''


# class SecuritiesSelector(QComboBox):
#     def __init__(self, data_utility, parent=None):
#         super(SecuritiesSelector, self).__init__(parent)
#
#         self.__data_utility = data_utility
#
#         self.__timer = QTimer()
#         self.__timer.setInterval(1000)
#         self.__timer.timeout.connect(self.on_timer)
#
#         if self.__data_utility is not None:
#             # Timer for update stock list
#             self.__timer.start()
#         self.setEditable(True)
#
#     def on_timer(self):
#         # Check stock list ready and update combobox
#         if self.__data_utility is not None and \
#                 self.__data_utility.stock_cache_ready():
#             stock_list = self.__data_utility.get_stock_list()
#             for stock_identity, stock_name in stock_list:
#                 self.addItem(stock_identity + ' | ' + stock_name, stock_identity)
#             self.__timer.stop()
#
#     def select_security(self, security: str, linkage: bool):
#         for index in range(self.count()):
#             stock_identity = self.itemData(index)
#             if stock_identity == security:
#                 self.setCurrentIndex(index)
#                 break
#
#     def get_input_securities(self) -> str:
#         input_securities = self.currentText()
#         if '|' in input_securities:
#             input_securities = input_securities.split('|')[0].strip()
#         return input_securities


# ----------------------------------------------------------------------------------------------------------------------

class SecuritiesPicker(QDialog):
    def __init__(self, sas_if: sasIF, parent=None):
        super(SecuritiesPicker, self).__init__(parent)

        self.__is_ok = False
        self.__select_list = []
        self.__sas_if: sasIF = sas_if

        self.__button_add = QPushButton('+')
        self.__button_del = QPushButton('-')
        self.__button_clear = QPushButton('X')
        self.__list_selected = QListWidget()
        if sas_if is not None:
            self.__combo_identity = SecuritiesSelector(sas_if)
        else:
            self.__combo_identity = QComboBox()
            # For test
            self.__select_list = ['000001.SZSE', '000002.SZSE', '000003.SZSE', '000004.SZSE',
                                  '600001.SZSE', '600002.SZSE', '600003.SZSE', '600004.SZSE']
            self.update_list()
        self.__button_ok = QPushButton('OK')
        self.__button_cancel = QPushButton('Cancel')

        self.init_ui()

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        line = QHBoxLayout()
        line.addWidget(self.__combo_identity, 100)
        line.addWidget(self.__button_add)
        main_layout.addLayout(line)

        line = QHBoxLayout()
        line.addWidget(self.__list_selected, 100)
        col = QVBoxLayout()
        col.addStretch()
        col.addWidget(self.__button_del)
        col.addWidget(self.__button_clear)
        col.addStretch()
        line.addLayout(col)
        main_layout.addLayout(line, 100)

        line = QHBoxLayout()
        line.addStretch()
        line.addWidget(self.__button_ok)
        line.addWidget(self.__button_cancel)
        main_layout.addLayout(line)

    def __config_control(self):
        self.setWindowFlags(int(self.windowFlags()) |
                            QtCore.Qt.WindowCloseButtonHint |
                            QtCore.Qt.WindowSystemMenuHint)
        self.__adjust_button_size(self.__button_add)
        self.__adjust_button_size(self.__button_del)
        self.__adjust_button_size(self.__button_clear)

        self.__button_add.setToolTip('Add to select list')
        self.__button_del.setToolTip('Remove select items from select list')
        self.__button_clear.setToolTip('Clear all selection from select list')

        self.__button_add.clicked.connect(self.on_button_add)
        self.__button_del.clicked.connect(self.on_button_del)
        self.__button_clear.clicked.connect(self.on_button_clear)

        self.__button_ok.clicked.connect(self.on_button_ok)
        self.__button_cancel.clicked.connect(self.on_button_cancel)

        self.__list_selected.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.setWindowTitle('Security Picker')
        self.setMinimumSize(QSize(600, 500))

    def __adjust_button_size(self, button: QPushButton):
        button.setMaximumSize(QSize(20, 20))

    def on_button_add(self):
        identity = self.__combo_identity.get_input_securities()
        if identity not in self.__select_list:
            self.__select_list.append(identity)
            self.update_list()

    def on_button_del(self):
        for item in self.__list_selected.selectedItems():
            if item.text() in self.__select_list:
                self.__select_list.remove(item.text())
        self.update_list()

    def on_button_clear(self):
        self.__select_list.clear()
        self.update_list()

    def on_button_ok(self):
        self.__is_ok = True
        self.close()

    def on_button_cancel(self):
        self.__is_ok = False
        self.close()

    def update_list(self):
        self.__list_selected.clear()
        for identity in self.__select_list:
            self.__list_selected.addItem(identity)

    # --------------------------------------------------------------------------

    def is_ok(self) -> bool:
        return self.__is_ok

    def get_selection(self) -> [str]:
        return self.__select_list

    def set_selection(self, selections: [str]):
        self.__select_list = selections
        self.update_list()


# ----------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    dlg = SecuritiesPicker(None)
    dlg.exec()


# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass



