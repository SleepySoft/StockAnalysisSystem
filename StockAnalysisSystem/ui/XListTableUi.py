#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2017/08/08
@file: DataTable.py
@function:
@modify:
"""
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QFileDialog, QComboBox

from ..core.Utiltity.ui_utility import *
from ..core.Database.XListTable import *
from ..core.Database.DatabaseEntry import *
from ..core.StockAnalysisSystem import StockAnalysisSystem


class XListTableUi(QWidget):

    class XListEditor(QWidget):
        def __init__(self):
            super(XListTableUi.XListEditor, self).__init__()

            self.__combo_name = QComboBox()
            self.__editor_reason = QTextEdit()
            self.__editor_comments = QTextEdit()

            self.init_ui()
            self.config_ui()

        def init_ui(self):
            main_layout = QVBoxLayout()
            self.setLayout(main_layout)

            main_layout.addWidget(QLabel('Name(*)'))
            main_layout.addWidget(self.__combo_name)

            main_layout.addWidget(QLabel('Reason'))
            main_layout.addWidget(self.__editor_reason)

            main_layout.addWidget(QLabel('Comments'))
            main_layout.addWidget(self.__editor_comments)

        def config_ui(self):
            data_utility = StockAnalysisSystem().get_data_hub_entry().get_data_utility()
            stock_list = data_utility.get_stock_list()
            for stock_identity, stock_name in stock_list:
                self.__combo_name.addItem(stock_identity + ' | ' + stock_name)
            self.__combo_name.setEditable(True)
            self.setMinimumSize(QSize(600, 400))

        def get_input(self) -> (str, str, str):
            stock_input = self.__combo_name.currentText()
            if '|' in stock_input:
                stock_input = stock_input.split('|')[0].strip()
            return stock_input,\
                   self.__editor_reason.toPlainText(),\
                   self.__editor_comments.toPlainText()

    # --------------------------------------------------------------------------------------

    def __init__(self, x_table: XListTable, title: str = ''):
        super(XListTableUi, self).__init__()

        self.__title = title
        self.__unsave = False
        self.__x_table = x_table
        self.__main_table = EasyQTableWidget(self)
        self.__translate = QtCore.QCoreApplication.translate

        self.__button_add_name = QPushButton(self.__translate('', 'Upsert'))
        self.__button_del_name = QPushButton(self.__translate('', 'Delete'))
        self.__button_import_csv = QPushButton(self.__translate('', 'Import'))
        self.__button_save = QPushButton(self.__translate('', 'Save'))
        self.__button_reload = QPushButton(self.__translate('', 'Reload'))
        self.__button_reset = QPushButton(self.__translate('', 'Reset'))

        self.init_ui()

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()
        self.__x_table.reload()
        self.__refresh()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(self.__main_table)

        sub_layout = QHBoxLayout()
        sub_layout.addWidget(self.__button_add_name)
        sub_layout.addWidget(self.__button_del_name)
        sub_layout.addWidget(self.__button_import_csv)
        sub_layout.addWidget(self.__button_save)
        sub_layout.addWidget(self.__button_reload)
        sub_layout.addWidget(self.__button_reset)
        main_layout.addLayout(sub_layout)

    def __config_control(self):
        self.__button_add_name.clicked.connect(self.on_button_add_name)
        self.__button_del_name.clicked.connect(self.on_button_del_name)
        self.__button_import_csv.clicked.connect(self.on_button_import_csv)
        self.__button_save.clicked.connect(self.on_button_save)
        self.__button_reload.clicked.connect(self.on_button_reload)
        self.__button_reset.clicked.connect(self.on_button_reset)
        self.setMinimumSize(800, 600)
        self.setWindowTitle(self.__title)

    # ---------------------------------------------------- UI Event ----------------------------------------------------

    def on_button_add_name(self):
        dlg = WrapperQDialog(XListTableUi.XListEditor(), True)
        dlg.exec()

        if dlg.is_ok():
            name, reason, comments = dlg.get_wrapped_wnd().get_input()
            if name == '':
                QMessageBox.warning(self, 'Input', '名字为必填项')
            else:
                self.__x_table.upsert_to_list(name, reason, comments)
                self.__unsave = True
                self.__refresh()

    def on_button_del_name(self):
        row = self.__main_table.GetCurrentRow()
        if len(row) > 0:
            name = row[0]
            self.__x_table.remove_from_list(name)
            self.__unsave = True
            self.__refresh()

    def on_button_import_csv(self):
        QMessageBox.information(self, self.__translate('', '格式说明'),
                                self.__translate('',
                                                 '导入的CSV文件需要包含以下三个列：\n' 
                                                 '1. name：添加到名单中的名字，比如股票ID\n' 
                                                 '2. reason: 加入此名单的原因，内容为可选\n' 
                                                 '3. comments: 其它信息，此内容为可选'),
                                QMessageBox.Ok)
        file_path, ok = QFileDialog.getOpenFileName(self, 'Load CSV file', '', 'CSV Files (*.csv);;All Files (*)')
        if ok:
            # csv_name_column_to_identity(file_path, 'name')
            ret = self.__x_table.import_csv(file_path, False)
            QMessageBox.information(self, self.__translate('', '执行结果'),
                                    self.__translate('',
                                                     '导入成功' if ret else '导入失败，请检查CSV文件格式'),
                                    QMessageBox.Ok)
            self.__unsave = True
            self.__refresh()

    def on_button_save(self):
        reply = QMessageBox.information(self, self.__translate('', '写入警告'),
                                        self.__translate('',
                                                         '你做的所有编辑将写入数据库，' 
                                                         '操作即时生效且无法回滚。\n是否确定？'),
                                        QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.__x_table.flush()
        self.__unsave = False

    def on_button_reload(self):
        reply = QMessageBox.information(self, self.__translate('', '读取警告'),
                                        self.__translate('',
                                                         '此操作会导致你所有未保存的编辑内容丢失。' 
                                                         '\n是否确定？'),
                                        QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.__x_table.reload()
        self.__unsave = False
        self.__refresh()

    def on_button_reset(self):
        reply = QMessageBox.information(self, self.__translate('', '操作警告'),
                                        self.__translate('',
                                                         '此操作会清空整个名单，'
                                                         '不过在你点击“保存”前不会影响数据库。\n' 
                                                         '\n是否确定？'),
                                        QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.__x_table.clear()
        self.__refresh()

    def hideEvent(self, event):
        if self.__unsave:
            reply = QMessageBox.question(self, self.__translate('', '保存提示'),
                                         self.__translate('', '有未保存内容，是否保存？\n'),
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.__x_table.flush()
                self.__unsave = False

    def showEvent(self, event):
        self.__x_table.reload()
        self.__refresh()
        self.__unsave = False

    def closeEvent(self, event):
        if not self.__unsave:
            event.accept()
        else:
            reply = QMessageBox.question(self, self.__translate('', '保存提示'),
                                         self.__translate('',
                                                          '有未保存内容，是否保存？\n'
                                                          '是：保存并退出\n' 
                                                          '否：不保存直接退出\n'
                                                          '取消：关闭此提示且不退出'),
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                         QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.__x_table.flush()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()

    # ---------------------------------------------------- pvivate -----------------------------------------------------

    def __refresh(self):
        df = self.__x_table.get_name_table()
        if df is not None:
            df_display = df.copy(False)
            write_df_to_qtable(df_display, self.__main_table)


# ----------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    dlg = WrapperQDialog(XListTableUi(DatabaseEntry().get_black_table(), '黑名单'), False)
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



