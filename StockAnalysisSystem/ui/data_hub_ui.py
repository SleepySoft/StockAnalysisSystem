import logging
import traceback

from os import sys, path

import openpyxl
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QLineEdit, QCheckBox, QWidget, QComboBox, QDateTimeEdit, QFileDialog, QRadioButton

from StockAnalysisSystem.core.Utility.common import *
from StockAnalysisSystem.core.Utility.ui_utility import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.ui.Utility.ui_context import UiContext
from StockAnalysisSystem.interface.interface import SasInterface as sasIF
from StockAnalysisSystem.core.Utility.TableViewEx import TableViewEx
from StockAnalysisSystem.core.Utility.securities_selector import SecuritiesPicker


class ExportUi(QDialog):
    TABLE_HEADER = ['', 'Field', 'Group By']
    INDEX_CHECK = 0

    FILL_GROUP = openpyxl.styles.PatternFill(patternType="solid", start_color="EE1111")

    def __init__(self, export_data: pd.DataFrame):
        super(ExportUi, self).__init__()
        self.__export_data = export_data

        self.__radio_vertical = QRadioButton('Vertical')
        self.__radio_horizon = QRadioButton('Horizon')
        self.__check_readable = QCheckBox('Readable')
        self.__button_export = QPushButton('Export')
        self.__table_field_config = TableViewEx()

        self.init_ui()
        self.update_table()

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(self.__table_field_config)

        line = QHBoxLayout()
        line.addStretch()
        line.addWidget(self.__radio_vertical)
        line.addWidget(self.__radio_horizon)
        line.addWidget(self.__check_readable)
        line.addWidget(self.__button_export)
        main_layout.addLayout(line)

    def __config_control(self):
        self.__radio_horizon.setChecked(True)
        self.__check_readable.setChecked(True)

        self.__button_export.clicked.connect(self.on_button_export)

        self.__table_field_config.SetColumn(ExportUi.TABLE_HEADER)
        self.__table_field_config.SetCheckableColumn(ExportUi.INDEX_CHECK)
        self.__table_field_config.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.setMinimumSize(QSize(350, 600))

    def on_button_export(self):
        group_by = []
        select_name = []
        for i in range(self.__table_field_config.RowCount()):
            if self.__table_field_config.GetItemCheckState(i, 0) == Qt.Checked:
                field_name = self.__table_field_config.GetItemData(i, 1)
                check_group = self.__table_field_config.GetItemData(i, 2)
                if check_group.isChecked():
                    group_by.append(field_name)
                select_name.append(field_name)

        if len(select_name) == 0:
            QMessageBox().information(self, 'Warning.', 'Please select export field.')
            return

        file_path, ok = QFileDialog().getSaveFileName(self, 'Select Export Excel Path', '',
                                                      'XLSX Files (*.xlsx);;All Files (*)')
        if ok:
            self.export_excel(file_path, self.__export_data, select_name, group_by,
                              self.__radio_vertical.isChecked(), self.__check_readable.isChecked())
            QMessageBox().information(self, 'Information.', 'Export finished. File saved at:\n  %s' % file_path)
            self.close()

    def update_table(self):
        columns = list(self.__export_data.columns)
        self.__table_field_config.Clear()
        self.__table_field_config.SetColumn(ExportUi.TABLE_HEADER)

        for field_name in columns:
            self.__table_field_config.AppendRow(['', field_name, ''])
            index = self.__table_field_config.RowCount() - 1

            check_group = QCheckBox('')
            self.__table_field_config.SetCellWidget(index, 2, check_group)

            self.__table_field_config.SetItemData(index, 1, field_name)
            self.__table_field_config.SetItemData(index, 2, check_group)
            self.__table_field_config.SetItemCheckState(index, 0, Qt.Checked)

    def export_excel(self, file_path: str, df: pd.DataFrame, fields: [str], group_by: [str],
                     vertical: bool = True, readable: bool = False):
        export_data = df[fields]
        if readable:
            # TODO: Add readable interface and make field radable
            pass

        wb = openpyxl.Workbook()
        ws = wb.active

        if len(group_by) > 0:
            write_row, write_col = 1, 1
            grouped_df = export_data.groupby(group_by)
            for group, df in grouped_df:
                cell = excel_cell(write_row, write_col)
                ws[cell] = str(group)
                ws[cell].fill = ExportUi.FILL_GROUP
                if vertical:
                    _, write_col = self.__write_df_to_excel_vertical(ws, df, 1, write_col + 1)
                else:
                    write_row, _ = self.__write_df_to_excel_horizon(ws, df, write_row + 1, 1)
        else:
            if vertical:
                self.__write_df_to_excel_vertical(ws, df, 1, 1)
            else:
                self.__write_df_to_excel_horizon(ws, df, 1, 1)

        wb.save(file_path)

    def __write_df_to_excel_vertical(self, ws, df: pd.DataFrame, start_row: int, start_col: int) -> (int, int):
        write_row = start_row
        write_col = start_col
        for field in df.columns:
            cell = excel_cell(write_row, write_col)
            ws[cell] = field
            write_col += 1

        write_col = start_col
        for field in df.columns:
            write_row = start_row + 1
            data_column = df[field]
            for item in data_column:
                cell = excel_cell(write_row, write_col)
                ws[cell] = str(item)
                write_row += 1
            write_col += 1
        return write_row, write_col

    def __write_df_to_excel_horizon(self, ws, df: pd.DataFrame, start_row: int, start_col: int) -> (int, int):
        write_row = start_row
        write_col = start_col
        for field in df.columns:
            cell = excel_cell(write_row, write_col)
            ws[cell] = field
            write_row += 1

        write_row = start_row
        for field in df.columns:
            write_col = start_col + 1
            data_column = df[field]
            for item in data_column:
                cell = excel_cell(write_row, write_col)
                ws[cell] = str(item)
                write_col += 1
            write_row += 1
        return write_row, write_col


class DataHubUi(QWidget):
    def __init__(self, context: UiContext):
        super(DataHubUi, self).__init__()

        self.__context = context
        self.__translate = QtCore.QCoreApplication.translate
        self.__select_list = []
        self.__query_result = pd.DataFrame()

        self.__combo_uri = QComboBox()

        self.__text_selected = QTextEdit('')
        self.__button_pick = QPushButton(self.__translate('', 'Select'))

        # self.__line_identity = QLineEdit()
        # if self.__context is not None:
        #     self.__combo_identity = SecuritiesSelector(context.get_sas_interface())
        # else:
        #     self.__combo_identity = QComboBox()

        self.__table_main = EasyQTableWidget()
        self.__datetime_since = QDateTimeEdit()
        self.__datetime_until = QDateTimeEdit()
        self.__button_query = QPushButton(self.__translate('', 'Query'))
        self.__button_export = QPushButton(self.__translate('', 'Export'))
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
        line.addWidget(self.__button_export, 1)
        main_layout.addLayout(line)

        main_layout.addWidget(self.__table_main)

    def __config_control(self):
        # self.__combo_uri.setEditable(True)
        self.__check_identity_enable.setChecked(True)
        self.__check_datetime_enable.setChecked(True)
        self.__datetime_since.setDateTime(default_since())
        self.__datetime_until.setDateTime(now())

        self.__button_pick.clicked.connect(self.on_button_pick)
        self.__button_query.clicked.connect(self.on_button_query)
        self.__button_export.clicked.connect(self.on_button_export)

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

        self.setMinimumSize(QSize(800, 600))

    def on_button_pick(self):
        if self.__context is not None:
            dlg = SecuritiesPicker(self.__context.get_sas_interface())
            dlg.set_selection(self.__select_list)
            dlg.exec()
            if dlg.is_ok():
                self.__select_list = dlg.get_selection()
                self.__update_selection_text()

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
        self.__query_result = result

    def on_button_export(self):
        if not self.__query_result.empty:
            dlg = ExportUi(self.__query_result)
            dlg.exec()
        else:
            QMessageBox().information(self, 'Warning', 'No data to export.')

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
















