import pandas as pd
from datetime import date
from os import sys, path

from PyQt5.QtWidgets import QWidget, QMainWindow
from PyQt5.QtWidgets import QApplication, QScrollBar, QSlider, QMenu

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QStyledItemDelegate, QTreeWidgetItem, QComboBox, QInputDialog, QFileDialog

from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidget, QHBoxLayout, QTableWidgetItem, \
    QWidget, QPushButton, QDockWidget, QLineEdit, QAction, qApp, QMessageBox, QDialog, QVBoxLayout, QLabel, QTextEdit, \
    QListWidget, QShortcut

root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Extension.History.core import *
    from Extension.History.editor import *
    from Extension.History.filter import *
    from Extension.History.indexer import *
    from Extension.History.viewer_ex import *
    from Extension.History.Utility.ui_utility import *

    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
    from stock_analysis_system import StockAnalysisSystem
except Exception as e:
    sys.path.append(root_path)

    from Extension.History.core import *
    from Extension.History.editor import *
    from Extension.History.filter import *
    from Extension.History.indexer import *
    from Extension.History.viewer_ex import *
    from Extension.History.Utility.ui_utility import *

    from DataHub.DataHubEntry import DataHubEntry
    from Database.DatabaseEntry import DatabaseEntry
    from stock_analysis_system import StockAnalysisSystem
finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------

class StockHistoryUi(QMainWindow):
    def __init__(self, sas: StockAnalysisSystem):
        super(StockHistoryUi, self).__init__()

        self.__sas = sas
        self.__history = History()
        self.__time_axis = TimeAxis()
        self.__time_axis.set_agent(self)
        self.__time_axis.set_history_core(self.__history)

        self.__combo_name = QComboBox()
        self.__button_ensure = QPushButton('确定')

        self.__init_ui()
        self.__config_ui()

    def __init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        group_box, group_layout = create_v_group_box('Securities')

        main_layout.addWidget(self.__time_axis)
        main_layout.addWidget(group_box)

        group_layout.addLayout(horizon_layout([
            'Securities', self.__combo_name, self.__button_ensure,
        ]))

    def __config_ui(self):
        data_utility = self.__sas.get_data_hub_entry().get_data_utility()
        stock_list = data_utility.get_stock_list()
        for stock_identity, stock_name in stock_list:
            self.__combo_name.addItem(stock_identity + ' | ' + stock_name, stock_identity)
        self.__combo_name.setEditable(True)
        self.setMinimumSize(QSize(600, 400))

        self.__button_ensure.clicked.connect(self.on_button_ensure)

    def on_button_ensure(self):
        stock_input = self.__combo_name.currentText()
        if '|' in stock_input:
            stock_input = stock_input.split('|')[0].strip()
        self.load_for_securities(stock_input)

    # ------------------------------- TimeAxis.Agent -------------------------------

    def on_r_button_up(self, pos: QPoint):
        pass

    # ------------------------------------------------------------------------------

    def load_for_securities(self, securities: str):
        base_path = path.dirname(path.abspath(__file__))
        history_path = path.join(base_path, 'History')
        depot_path = path.join(history_path, 'depot')
        his_file = path.join(depot_path, securities + '.his')
        trade_data = self.__sas.get_data_hub_entry().get_data_center().query('TradeData.Stock.Daily', securities)


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': 'b3767a36-123f-45ab-bfad-f352c2b48354',
        'plugin_name': 'History',
        'plugin_version': '0.0.0.1',
        'tags': ['History', 'Sleepy'],
    }


def plugin_adapt(method: str) -> bool:
    return method in ['widget']


def plugin_capacities() -> list:
    return [
        'widget',
    ]


# ----------------------------------------------------------------------------------------------------------------------

sasEntry = None


def init(sas: StockAnalysisSystem):
    try:
        global sasEntry
        sasEntry = sas
        from Extension.History.main import HistoryUi
        main_wnd = HistoryUi()
    except Exception as e:
        main_wnd = None
    finally:
        pass
    return main_wnd


def period():
    pass


def thread():
    pass


def widget() -> QWidget:
    pass


















