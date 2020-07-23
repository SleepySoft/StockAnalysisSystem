from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QTimer, QSortFilterProxyModel
from PyQt5.QtWidgets import QCompleter, QComboBox
from StockAnalysisSystem.core.DataHub.DataUtility import DataUtility


class SecuritiesSelector(QComboBox):
    def __init__(self, data_utility: DataUtility, parent=None):
        super(SecuritiesSelector, self).__init__(parent)

        self.__data_utility: DataUtility = data_utility

        self.__timer = QTimer()
        self.__timer.setInterval(1000)
        self.__timer.timeout.connect(self.on_timer)

        if self.__data_utility is not None:
            # Timer for update stock list
            self.__timer.start()

        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable(True)

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
        if self.__data_utility is not None and \
                self.__data_utility.stock_cache_ready():
            stock_list = self.__data_utility.get_stock_list()
            for stock_identity, stock_name in stock_list:
                self.addItem(stock_identity + ' | ' + stock_name, stock_identity)
            self.__timer.stop()

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


