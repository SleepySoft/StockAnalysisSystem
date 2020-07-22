import os
import errno

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QTimer, QDateTime, QPoint, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QButtonGroup, QDateTimeEdit, QApplication, QLabel, QTextEdit, QPushButton, QVBoxLayout, \
    QMessageBox, QWidget, QComboBox, QCheckBox, QRadioButton, QLineEdit, QAbstractItemView, QFileDialog, QDialog
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent

from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.TagsLib import *
from StockAnalysisSystem.core.Utiltity.CsvRecord import *
from StockAnalysisSystem.core.Utiltity.ui_utility import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.TableViewEx import TableViewEx
from StockAnalysisSystem.core.Utiltity.securities_selector import SecuritiesSelector
from StockAnalysisSystem.core.DataHub.DataUtility import DataUtility

try:
    from .MemoUtility import *
except Exception as e:
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.append(root_path)

    from StockMemo.MemoUtility import *
finally:
    pass


# -------------------------------------------------- class BlackList ---------------------------------------------------

class BlackList:
    BLACK_LIST_TAGS = '黑名单'
    RECORD_CLASSIFY = 'black_list'

    def __init__(self, memo_data: StockMemoData):
        self.__memo_data = memo_data
        self.__stock_tag: Tags = memo_data.get_data('tags') if memo_data is not None else None
        self.__memo_record: CsvRecord = memo_data.get_memo_record() if memo_data is not None else None

        self.__data_loaded = False
        self.__black_list_securities: list = []
        self.__black_list_record: pd.DataFrame = None

    # ----------------------------------------------------

    def save_black_list(self):
        if self.__data_valid() and self.__data_loaded:
            self.__stock_tag.save()
            self.__memo_record.save()
            self.__memo_data.broadcast_data_updated('tags')
            self.__memo_data.broadcast_data_updated('memo_record')

    def add_to_black_list(self, security: str, reason: str):
        if self.__data_valid() and self.__data_loaded:
            return
        if security in self.__black_list_securities:
            return
        self.__memo_record.add_record({
            'time': now(),
            'security': security,
            'brief': '加入黑名单',
            'content': '加入黑名单: %s' % reason,
            'classify': BlackList.RECORD_CLASSIFY,
        }, False)
        self.__stock_tag.add_obj_tags(security, BlackList.BLACK_LIST_TAGS)

    def remove_from_black_list(self, security: str, reason: str):
        if security not in self.__black_list_securities:
            return
        self.__memo_record.add_record({
            'time': now(),
            'security': security,
            'brief': '移除黑名单',
            'content': '移除黑名单: ' % reason,
            'classify': BlackList.RECORD_CLASSIFY,
        }, False)
        self.__stock_tag.remove_obj_tags(security, BlackList.BLACK_LIST_TAGS)

    def get_black_list_data(self) -> pd.DataFrame:
        return self.__black_list_record

    def reload_black_list_data(self):
        self.__collect_black_list_data()

    # ---------------------------------------------------------------------------------

    def __data_valid(self) -> bool:
        return self.__memo_data is not None and self.__stock_tag is not None and self.__memo_record is not None

    def __collect_black_list_data(self):
        if self.__data_valid:
            black_list_securities = self.__stock_tag.objs_from_tags('黑名单') if self.__stock_tag is not None else []
            df = self.__memo_record.get_records({'classify': BlackList.RECORD_CLASSIFY})
            if df is not None and not df.empty:
                df = df.sort_values('time')
                df = df.groupby('security').last()
                df = df[df['security'] in black_list_securities]
            self.__black_list_securities = black_list_securities
            self.__black_list_record = df
            self.__data_loaded = True


# ------------------------------------------------- class BlackListUi --------------------------------------------------

class BlackListUi(QWidget):
    HEADER = ['Code', 'Name', 'Reason']

    class BlackListEditor(QWidget):
        def __init__(self, data_utility: DataUtility):
            self.__data_utility = data_utility
            super(BlackListUi.BlackListEditor, self).__init__()

            self.__stock_selector = \
                SecuritiesSelector(self.__data_utility) if self.__data_utility is not None else QComboBox()
            self.__editor_reason = QTextEdit()

            self.init_ui()
            self.config_ui()

        def init_ui(self):
            main_layout = QVBoxLayout()
            self.setLayout(main_layout)

            main_layout.addWidget(QLabel('Security: '))
            main_layout.addWidget(self.__stock_selector)

            main_layout.addWidget(QLabel('Reason: '))
            main_layout.addWidget(self.__editor_reason)

        def config_ui(self):
            self.setMinimumSize(QSize(600, 400))

        def get_input(self) -> (str, str):
            return self.__stock_selector.get_select_securities(), \
                   self.__editor_reason.toPlainText()

    def __init__(self, black_list: BlackList, data_utility: DataUtility):
        self.__black_list = black_list
        self.__data_utility = data_utility
        super(BlackListUi, self).__init__()

        self.__black_list_table = TableViewEx()

        self.__button_add = QPushButton('Add')
        self.__button_import = QPushButton('Import')
        self.__button_analysis = QPushButton('Analysis')
        self.__button_remove = QPushButton('Remove')

        self.init_ui()
        self.config_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.__black_list_table, 9)
        layout.addLayout(horizon_layout([QLabel(''), self.__button_add, self.__button_import,
                                         self.__button_analysis, self.__button_remove],
                                        [10, 1, 1, 1, 1]))

    def config_ui(self):
        self.setMinimumSize(800, 600)
        self.setWindowTitle('黑名单管理')

        self.__black_list_table.SetColumn(BlackListUi.HEADER)
        self.__black_list_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__black_list_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.__black_list_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.__black_list_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.__button_add.clicked.connect(self.__on_button_add)
        self.__button_import.clicked.connect(self.__on_button_import)
        self.__button_analysis.clicked.connect(self.__on_button_analysis)
        self.__button_remove.clicked.connect(self.__on_button_remove)

    def __on_button_add(self):
        dlg = WrapperQDialog(BlackListUi.BlackListEditor(self.__data_utility), True)
        dlg.setWindowTitle('加入黑名单')
        dlg.exec()

        if dlg.is_ok():
            security, reason = dlg.get_wrapped_wnd().get_input()
            if security == '':
                QMessageBox.warning(self, 'Input', '请选择股票')
                return
            if self.__black_list is not None:
                self.__black_list.add_to_black_list(security, reason)

    def __on_button_import(self):
        QMessageBox.information(self, '格式说明','导入的CSV文件需要包含以下两个列：\n' 
                                                 '1. name：添加到名单中的股票ID\n' 
                                                 '2. reason: 加入此名单的原因，内容为可选\n',
                                QMessageBox.Ok)
        file_path, ok = QFileDialog.getOpenFileName(self, 'Load CSV file', '', 'CSV Files (*.csv);;All Files (*)')
        if ok:
            pass

    def __on_button_analysis(self):
        pass

    def __on_button_remove(self):
        row = self.__black_list_table.GetSelectRows()
        if len(row) > 0:
            security = self.__black_list_table.GetItemText(row[0], 0)
            self.__black_list.remove_from_black_list(security, '手工删除')

    def update_table(self):
        self.__black_list_table.Clear()
        self.__black_list_table.SetColumn(BlackListUi.HEADER)

        black_list_data = self.__black_list.get_black_list_data()

        for index, row in black_list_data.iterrows():
            self.__memo_table.AppendRow([
                row['security'],
                self.__data_utility.stock_identity_to_name(row['security']),
                row['content'],
            ])


# ------------------------------------------------ File Entry : main() -------------------------------------------------

def main():
    app = QApplication(sys.argv)

    black_list = BlackList(None)
    black_list_ui = BlackListUi(black_list, None)
    black_list_ui.show()

    exit(app.exec_())


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










