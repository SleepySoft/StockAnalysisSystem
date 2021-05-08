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
from os import sys
from PyQt5.QtWidgets import QGridLayout, QLineEdit, QRadioButton
from StockAnalysisSystem.core.Utility.ui_utility import *


class InterfaceSelectUi(QWidget):
    def __init__(self, inited: bool = True):
        super(InterfaceSelectUi, self).__init__()
        
        self.__radio_remote_if = QRadioButton('Remote Interface')
        self.__radio_local_if = QRadioButton('Local Interface')

        self.__line_remote_if_host = QLineEdit('http://127.0.0.1:80/api')
        self.__line_remote_if_port = QLineEdit()
        self.__line_remote_if_user = QLineEdit()
        self.__line_remote_if_pass = QLineEdit()
        self.__line_remote_if_token = QLineEdit('Any but not empty (see access_control.py)')

        self.__button_ok = QPushButton('OK')
        self.__button_exit = QPushButton('Exit')

        self.__is_ok = False
        self.__is_local = True
        self.__host_uri = ''
        self.__host_port = ''
        self.__auth_user = ''
        self.__auth_pass = ''
        self.__auth_token = ''

        self.init_ui()

    # ------------------------------------------------------------------------------------------------------------------

    def is_ok(self) -> bool:
        return self.__is_ok

    def is_local(self) -> bool:
        return self.__is_local

    def get_remote_host_config(self) -> (str, str):
        return self.__host_uri, self.__host_port

    def get_remote_host_authentication(self) -> (str, str, str):
        return self.__auth_user, self.__auth_pass, self.__auth_token

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QGridLayout()
        self.setLayout(main_layout)
        self.setMinimumSize(400, 200)

        main_layout.addWidget(self.__radio_remote_if, 0, 0)
        main_layout.addWidget(self.__radio_local_if, 0, 1)

        main_layout.addWidget(QLabel('Remote interface Host: '), 1, 0)
        main_layout.addWidget(self.__line_remote_if_host, 1, 1)

        main_layout.addWidget(QLabel('Remote interface Port: '), 2, 0)
        main_layout.addWidget(self.__line_remote_if_port, 2, 1)

        main_layout.addWidget(QLabel('Remote interface User: '), 3, 0)
        main_layout.addWidget(self.__line_remote_if_user, 3, 1)

        main_layout.addWidget(QLabel('Remote interface Pass: '), 4, 0)
        main_layout.addWidget(self.__line_remote_if_pass, 4, 1)

        main_layout.addWidget(QLabel('Remote interface Token: '), 5, 0)
        main_layout.addWidget(self.__line_remote_if_token, 5, 1)

        button_area = QHBoxLayout()
        button_area.addStretch()
        button_area.addWidget(self.__button_ok)
        button_area.addWidget(self.__button_exit)
        main_layout.addLayout(button_area, 6, 0)

    def __config_control(self):
        self.setWindowTitle('Interface Selector')

        self.__radio_remote_if.setChecked(True)
        self.__line_remote_if_pass.setEchoMode(QLineEdit.Password)
        self.__radio_remote_if.clicked.connect(self.__on_radio_remote)

        self.__radio_local_if.clicked.connect(self.__on_radio_local)

        self.__button_ok.clicked.connect(self.__on_button_ok)
        self.__button_exit.clicked.connect(self.__on_button_exit)

    def __on_radio_remote(self):
        self.__enable_host_setting(True)

    def __on_radio_local(self):
        self.__enable_host_setting(False)

    def __on_button_ok(self):
        self.__is_ok = True
        self.__is_local = self.__radio_local_if.isChecked()
        self.__host_uri = self.__line_remote_if_host.text()
        self.__host_port = self.__line_remote_if_port.text()
        self.__auth_user = self.__line_remote_if_user.text()
        self.__auth_pass = self.__line_remote_if_pass.text()
        self.__auth_token = self.__line_remote_if_token.text()
        self.close()

    def __on_button_exit(self):
        sys.exit(0)

    def __enable_host_setting(self, enable: bool):
        self.__line_remote_if_host.setEnabled(enable)
        self.__line_remote_if_port.setEnabled(enable)
        self.__line_remote_if_user.setEnabled(enable)
        self.__line_remote_if_pass.setEnabled(enable)
        self.__line_remote_if_token.setEnabled(enable)


# ----------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    dlg = WrapperQDialog(InterfaceSelectUi())
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


