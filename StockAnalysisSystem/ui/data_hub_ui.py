import logging
import traceback

from os import sys, path

from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QLineEdit, QCheckBox, QWidget, QComboBox, QDateTimeEdit

from StockAnalysisSystem.core.Utility.common import *
from StockAnalysisSystem.core.Utility.ui_utility import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.ui.Utility.ui_context import UiContext
from StockAnalysisSystem.interface.interface import SasInterface as sasIF
from StockAnalysisSystem.core.Utility.securities_selector import SecuritiesPicker


class DataHubUi(QWidget):
    def __init__(self, context: UiContext):
        super(DataHubUi, self).__init__()

        self.__context = context
        self.__translate = QtCore.QCoreApplication.translate
        self.__select_list = []

        self.__combo_uri = QComboBox()

        self.__text_selected = QTextEdit('')
        self.__button_pick = QPushButton('Select')

        # self.__line_identity = QLineEdit()
        # if self.__context is not None:
        #     self.__combo_identity = SecuritiesSelector(context.get_sas_interface())
        # else:
        #     self.__combo_identity = QComboBox()

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
        line.addWidget(self.__text_selected, 10)
        line.addWidget(self.__button_pick, 0)
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
        self.__button_pick.clicked.connect(self.on_button_pick)

        if self.__context is not None:
            data_agents = self.__context.get_sas_interface().sas_get_data_agent_probs()
            all_uri = [da.get('uri', '') for da in data_agents]
            for uri in all_uri:
                self.__combo_uri.addItem(uri)

        font = self.__text_selected.font()
        font_m = QFontMetrics(font)
        text_height = font_m.lineSpacing()
        self.__text_selected.setFixedHeight(3 * text_height)
        self.__text_selected.setEnabled(False)

    def on_button_query(self):
        uri = self.__combo_uri.currentText()
        # identity = self.__line_identity.text() if self.__check_identity_enable.isChecked() else None
        # identity = self.__combo_identity.get_input_securities() if self.__check_identity_enable.isChecked() else None

        identity = self.__select_list if (self.__check_identity_enable.isChecked() and
                                          len(self.__select_list) > 0) else None
        since = self.__datetime_since.dateTime().toPyDateTime() if self.__check_datetime_enable.isChecked() else None
        until = self.__datetime_until.dateTime().toPyDateTime() if self.__check_datetime_enable.isChecked() else None

        if self.__context is not None:
            result = self.__context.get_sas_interface().sas_query(uri, identity, (since, until))

        if result is not None and '_id' in result.columns:
            del result['_id']
            write_df_to_qtable(result, self.__table_main)

    def on_button_pick(self):
        if self.__context is not None:
            dlg = SecuritiesPicker(self.__context.get_sas_interface())
            dlg.set_selection(self.__select_list)
            dlg.exec()
            if dlg.is_ok():
                self.__select_list = dlg.get_selection()
                self.__update_selection_text()

    def __update_selection_text(self):
        self.__text_selected.setText(', '.join(self.__select_list))


# ----------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    dlg = WrapperQDialog(DataHubUi(None))
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
















