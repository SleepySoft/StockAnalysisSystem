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
import traceback
import threading
from os import sys, path, system

from PyQt5.QtCore import pyqtSignal, QProcess
from PyQt5.QtWidgets import QGridLayout, QLineEdit, QFileDialog, QComboBox

from StockAnalysisSystem.core.Utility.ui_utility import *
from StockAnalysisSystem.interface.interface import SasInterface as sasIF


class QStringList(object):
    pass


class ConfigUi(QWidget):
    check_finish_signal = pyqtSignal()

    def __init__(self, config: dict = None):
        super(ConfigUi, self).__init__()

        # self.__inited = inited
        self.__config = {} if config is None else config

        self.__line_ts_token = QLineEdit()
        self.__line_nosql_db_host = QLineEdit('localhost')
        self.__line_nosql_db_port = QLineEdit('27017')
        self.__line_nosql_db_user = QLineEdit()
        self.__line_nosql_db_pass = QLineEdit()

        if sys.platform == 'linux':
            self.__line_mongo_db_binary = QLineEdit('/bin')
        else:
            self.__line_mongo_db_binary = QLineEdit('C:\\Program Files\\MongoDB\Server\\4.0\\bin')
        self.__button_browse = QPushButton('Browse')
        self.__button_import = QPushButton('Import')
        self.__button_export = QPushButton('Export')

        self.__combo_web_proxy_protocol = QComboBox()
        self.__line_web_proxy_host = QLineEdit('')

        self.__button_ok = QPushButton('OK')
        self.__button_exit = QPushButton('Exit')
        self.__text_information = QTextEdit()
        # self.__label_information = QLabel()

        # Command
        self.__process = None
        self.__pending_command = []

        self.init_ui()

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QGridLayout()
        self.setLayout(main_layout)
        self.setMinimumSize(600, 400)

        main_layout.addWidget(QLabel('NoSql Host: '), 0, 0)
        main_layout.addWidget(self.__line_nosql_db_host, 0, 1)

        main_layout.addWidget(QLabel('NoSql Port: '), 0, 2)
        main_layout.addWidget(self.__line_nosql_db_port, 0, 3)

        main_layout.addWidget(QLabel('NoSql User: '), 1, 0)
        main_layout.addWidget(self.__line_nosql_db_user, 1, 1)

        main_layout.addWidget(QLabel('NoSql Pass: '), 1, 2)
        main_layout.addWidget(self.__line_nosql_db_pass, 1, 3)

        main_layout.addWidget(QLabel('Ts Token: '), 2, 0)
        main_layout.addWidget(self.__line_ts_token, 2, 1, 1, 3)

        main_layout.addWidget(QLabel('MongoDB bin: '), 3, 0)
        mongodb_area = QHBoxLayout()
        mongodb_area.addWidget(self.__line_mongo_db_binary)
        mongodb_area.addWidget(self.__button_browse)
        mongodb_area.addWidget(self.__button_export)
        mongodb_area.addWidget(self.__button_import)
        main_layout.addLayout(mongodb_area, 3, 1, 1, 3)

        main_layout.addWidget(QLabel('Internet Proxy: '), 4, 0)
        main_layout.addWidget(self.__combo_web_proxy_protocol, 4, 1)
        main_layout.addWidget(self.__line_web_proxy_host, 4, 2, 1, 2)

        main_layout.addWidget(QLabel('Status: '), 5, 0)
        button_area = QHBoxLayout()
        button_area.addWidget(self.__button_ok)
        button_area.addWidget(self.__button_exit)
        main_layout.addLayout(button_area, 5, 3)

        main_layout.addWidget(self.__text_information, 6, 0, 1, 4)

    def __config_control(self):
        self.setWindowTitle('System Config')
        self.__button_ok.clicked.connect(self.on_button_ok)
        self.__button_exit.clicked.connect(self.on_button_exit)
        self.__button_browse.clicked.connect(self.on_button_browse)
        self.__button_import.clicked.connect(self.on_button_import)
        self.__button_export.clicked.connect(self.on_button_export)

        # self.__text_information.setEnabled(False)
        self.__text_information.setStyleSheet("QLabel{border:2px solid rgb(0, 0, 0);}")
        self.__text_information.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)

        self.__combo_web_proxy_protocol.setEditable(True)
        self.__combo_web_proxy_protocol.addItem('HTTP_PROXY')
        self.__combo_web_proxy_protocol.addItem('HTTPS_PROXY')

        # sas = StockAnalysisSystem()
        # logs = sas.get_log_errors()

        self.__config_to_ui()
        # self.__text_information.setText('\n'.join(logs))

    def on_button_ok(self):
        self.__ui_to_config()
        self.close()

    def on_button_exit(self):
        # if not self.__inited:
        #     sys.exit(0)
        # else:
        self.close()

    def on_button_browse(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select MongoDB Binary Directory",
                                                      directory=self.__line_mongo_db_binary.text()))
        if folder == '':
            return
        self.__line_mongo_db_binary.setText(folder)

    def on_button_import(self):
        if not self.__check_alarm_mongodb_config():
            return
        folder = str(QFileDialog.getExistingDirectory(self, "Select MongoDB Data Directory",
                                                      directory=path.dirname(path.abspath(__file__))))
        if folder == '':
            return

        folder_name = path.basename(path.normpath(folder))
        if folder_name not in ['StockAnalysisSystem', 'StockDaily', 'SasCache']:
            QMessageBox.information(self,
                                    QtCore.QCoreApplication.translate('main', '错误的数据'),
                                    QtCore.QCoreApplication.translate('main', '数据必须为StockAnalysisSystem或StockDaily之一'),
                                    QMessageBox.Ok, QMessageBox.Ok)
            return

        tips = QtCore.QCoreApplication.translate('main', '准备导入数据库：') + folder_name + \
               QtCore.QCoreApplication.translate('main', '\n此数据库中的数据将会被全部改写\n是否确认？')
        reply = QMessageBox.question(self,
                                     QtCore.QCoreApplication.translate('main', '导入确认'), tips,
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        mongodb_name = folder_name
        mongodb_bin = self.__line_mongo_db_binary.text()
        mongodb_host = self.__line_nosql_db_host.text()
        mongodb_port = self.__line_nosql_db_port.text()

        if sys.platform == 'linux':
            import_binary = path.join(mongodb_bin, 'mongorestore')
        else:
            import_binary = path.join(mongodb_bin, 'mongorestore.exe')
        import_command = '"' + import_binary + '"' + \
                         ' --drop '\
                         ' --host ' + mongodb_host + \
                         ' --port ' + mongodb_port + \
                         ' -d ' + mongodb_name + \
                         ' --dir ' + folder + \
                         self.__generate_auth_parameters()
        self.execute_command(import_command)

    def on_button_export(self):
        if not self.__check_alarm_mongodb_config():
            return
        folder = str(QFileDialog.getExistingDirectory(self, "Select MongoDB Data Directory",
                                                      directory=path.dirname(path.abspath(__file__))))
        if folder == '':
            return
        mongodb_bin = self.__line_mongo_db_binary.text()
        mongodb_host = self.__line_nosql_db_host.text()
        mongodb_port = self.__line_nosql_db_port.text()

        if sys.platform == 'linux':
            export_binary = path.join(mongodb_bin, 'mongodump')
        else:
            export_binary = path.join(mongodb_bin, 'mongodump.exe')

        self.execute_commands([
            self.__generate_export_command(export_binary, mongodb_host, mongodb_port, folder, 'SasCache'),
            self.__generate_export_command(export_binary, mongodb_host, mongodb_port, folder, 'StockDaily'),
            self.__generate_export_command(export_binary, mongodb_host, mongodb_port, folder, 'StockAnalysisSystem'),
        ])

    def __generate_export_command(self, export_binary: str, mongodb_host: str,
                                  mongodb_port: str, folder: str, db_name: str) -> str:
        return '"' + export_binary + '"' + \
               ' -h ' + mongodb_host + ':' + mongodb_port + \
               ' -d ' + db_name + \
               ' -o ' + folder + \
               self.__generate_auth_parameters()

    def __generate_auth_parameters(self) -> str:
        mongodb_user = self.__line_nosql_db_user.text()
        mongodb_pass = self.__line_nosql_db_pass.text()
        auth_param = ''
        if mongodb_user != '':
            auth_param += ' -u ' + mongodb_user
        if mongodb_pass != '':
            auth_param += ' -p ' + mongodb_pass
        return auth_param

    # -----------------------------------------------------------------------------------

    def edit_config(self, config: dict):
        self.__config = config

    def get_config(self) -> dict:
        return self.__config

    # -----------------------------------------------------------------------------------

    def __config_to_ui(self):
        # sas = StockAnalysisSystem()
        # config = sas.get_config()

        self.__line_ts_token.setText(self.__config.get('TS_TOKEN', ''))

        self.__line_nosql_db_host.setText(self.__config.get('NOSQL_DB_HOST', ''))
        self.__line_nosql_db_port.setText(self.__config.get('NOSQL_DB_PORT', ''))
        self.__line_nosql_db_user.setText(self.__config.get('NOSQL_DB_USER', ''))
        self.__line_nosql_db_pass.setText(self.__config.get('NOSQL_DB_PASS', ''))

        self.__combo_web_proxy_protocol.setEditText(self.__config.get('PROXY_PROTOCOL', ''))
        self.__combo_web_proxy_protocol.setCurrentIndex(0)
        self.__line_web_proxy_host.setText(self.__config.get('PROXY_HOST', ''))

    def __ui_to_config(self):
        config = {
            'TS_TOKEN': self.__line_ts_token.text(),
            'NOSQL_DB_HOST': self.__line_nosql_db_host.text(),
            'NOSQL_DB_PORT': self.__line_nosql_db_port.text(),
            'NOSQL_DB_USER': self.__line_nosql_db_user.text(),
            'NOSQL_DB_PASS': self.__line_nosql_db_pass.text(),

            'PROXY_PROTOCOL': self.__combo_web_proxy_protocol.currentText(),
            'PROXY_HOST': self.__line_web_proxy_host.text(),
        }

    def __check_alarm_mongodb_config(self) -> bool:
        if self.__line_mongo_db_binary.text().strip() == '':
            QMessageBox.information(self,
                                    QtCore.QCoreApplication.translate('main', 'MongoDB配置错误'),
                                    QtCore.QCoreApplication.translate('main', '请先设置MongoDB的bin目录'),
                                    QMessageBox.Ok, QMessageBox.Ok)
            return False
        if self.__line_nosql_db_host.text().strip() == '':
            QMessageBox.information(self,
                                    QtCore.QCoreApplication.translate('main', 'MongoDB配置错误'),
                                    QtCore.QCoreApplication.translate('main', '请先设置MongoDB的服务器地址'),
                                    QMessageBox.Ok, QMessageBox.Ok)
            return False
        if self.__line_nosql_db_port.text().strip() == '':
            QMessageBox.information(self,
                                    QtCore.QCoreApplication.translate('main', 'MongoDB配置错误'),
                                    QtCore.QCoreApplication.translate('main', '请先设置MongoDB的服务器端口'),
                                    QMessageBox.Ok, QMessageBox.Ok)
            return False
        return True

    # ------------------------------------------- Command execute -------------------------------------------

    def execute_commands(self, commands: [str]):
        if len(self.__pending_command) > 0:
            self.__pending_command.extend(commands)
        else:
            self.__pending_command = commands
            self.execute_pending_commands()

    def execute_pending_commands(self) -> bool:
        if len(self.__pending_command) > 0:
            cmd = self.__pending_command.pop(0)
            self.execute_command(cmd)
            return True
        else:
            return False

    def execute_command(self, cmd: str):
        tips = 'Execute command:　' + cmd
        self.__text_information.append(tips)
        print(tips)

        self.__process = QProcess()
        self.__process.setProcessChannelMode(QProcess.MergedChannels)
        self.__process.started.connect(self.on_command_start)
        self.__process.finished.connect(self.on_command_finished)
        self.__process.readyReadStandardOutput.connect(self.read_output)
        self.__process.start(cmd)

    def on_command_start(self):
        tips = 'Process started...'
        self.__text_information.append(tips)
        print(tips)

    def on_command_finished(self):
        if self.execute_pending_commands():
            return
        tips = 'Process finished...'
        print(tips)
        self.__text_information.append(tips)
        self.__text_information.append('导入完成')

    def read_output(self):
        output = bytes(self.__process.readAllStandardOutput()).decode('UTF-8').strip()
        self.__text_information.append(output)


# ----------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    dlg = WrapperQDialog(ConfigUi())
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






