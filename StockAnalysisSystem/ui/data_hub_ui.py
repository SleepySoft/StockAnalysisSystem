import logging
import traceback

from os import sys, path
from PyQt5.QtWidgets import QLineEdit, QCheckBox, QWidget, QComboBox, QDateTimeEdit

from StockAnalysisSystem.core.Utility.common import *
from StockAnalysisSystem.core.Utility.ui_utility import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.ui.Utility.ui_context import UiContext
from StockAnalysisSystem.interface.interface import SasInterface as sasIF


class DataHubUi(QWidget):
    def __init__(self, context: UiContext):
        super(DataHubUi, self).__init__()

        self.__context = context
        self.__translate = QtCore.QCoreApplication.translate

        self.__combo_uri = QComboBox()
        self.__line_identity = QLineEdit()
        self.__table_main = EasyQTableWidget()
        self.__datetime_since = QDateTimeEdit()
        self.__datetime_until = QDateTimeEdit()
        self.__button_query = QPushButton(self.__translate('', 'Query'))
        self.__check_identity_enable = QCheckBox(self.__translate('', 'Identity'))
        self.__check_datetime_enable = QCheckBox(self.__translate('', 'Datetime'))

        self.init_ui()

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        line = QHBoxLayout()
        line.addWidget(QLabel(self.__translate('', 'URI')), 0)
        line.addWidget(self.__combo_uri, 10)
        main_layout.addLayout(line)

        line = QHBoxLayout()
        line.addWidget(self.__check_identity_enable, 0)
        line.addWidget(self.__line_identity, 10)
        main_layout.addLayout(line)

        line = QHBoxLayout()
        line.addWidget(self.__check_datetime_enable, 0)
        line.addWidget(self.__datetime_since, 10)
        line.addWidget(self.__datetime_until, 10)
        main_layout.addLayout(line)

        line = QHBoxLayout()
        line.addWidget(QLabel(' '), 10)
        line.addWidget(self.__button_query, 1)
        main_layout.addLayout(line)

        main_layout.addWidget(self.__table_main)

    def __config_control(self):
        # self.__combo_uri.setEditable(True)
        self.__check_identity_enable.setChecked(True)
        self.__check_datetime_enable.setChecked(True)
        self.__datetime_since.setDateTime(default_since())
        self.__datetime_until.setDateTime(now())
        self.__button_query.clicked.connect(self.on_button_query)

        data_agents = self.__context.get_sas_interface().sas_get_data_agent_probs()
        all_uri = [da.get('uri', '') for da in data_agents]
        for uri in all_uri:
            self.__combo_uri.addItem(uri)

    def on_button_query(self):
        uri = self.__combo_uri.currentText()
        identity = self.__line_identity.text() if self.__check_identity_enable.isChecked() else None
        since = self.__datetime_since.dateTime().toPyDateTime() if self.__check_datetime_enable.isChecked() else None
        until = self.__datetime_until.dateTime().toPyDateTime() if self.__check_datetime_enable.isChecked() else None

        result = self.__context.get_sas_interface().sas_query(uri, identity, (since, until))

        if result is not None and '_id' in result.columns:
            del result['_id']
            write_df_to_qtable(result, self.__table_main)


# ----------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    data_hub = sas.get_data_hub_entry()
    data_center = data_hub.get_data_center()
    dlg = WrapperQDialog(DataHubUi(data_center))
    dlg.exec()


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
















