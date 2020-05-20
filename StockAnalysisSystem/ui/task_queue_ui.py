#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2017/08/08
@file: task_queue.py
@function:
@modify:
"""
import copy
import traceback
import threading

from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtCore import QTimer, pyqtSignal

from ..core.Utiltity.ui_utility import *


# ---------------------------------------------------- self ----------------------------------------------------

class TaskQueueUi(QWidget):
    observe_signal = pyqtSignal([str])

    INDEX_CHECK = 0
    INDEX_NAME = 1
    INDEX_IDENTITY = 2
    INDEX_ACTION = 3
    TABLE_HEADER = ['', 'Task Name', 'Task Identity', 'Action']

    def __init__(self, task_queue):
        super(TaskQueueUi, self).__init__()

        self.__task_queue = task_queue
        self.observe_signal.connect(self.__on_observe_signal)

        # UI related
        self.__table_main = EasyQTableWidget()

        self.init_ui()
        self.update_table()

        if self.__task_queue is not None:
            self.__task_queue.add_observer(self)

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.setMinimumSize(600, 400)
        main_layout.addWidget(self.__table_main)

    def __config_control(self):
        for _ in self.TABLE_HEADER:
            self.__table_main.insertColumn(0)
        self.__table_main.setHorizontalHeaderLabels(self.TABLE_HEADER)
        self.__table_main.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    # ---------------------------------------- Table Update ----------------------------------------

    def update_table(self):
        self.__table_main.clear()
        self.__table_main.setRowCount(0)
        self.__table_main.setHorizontalHeaderLabels(self.TABLE_HEADER)

        if self.__task_queue is None:
            return
        tasks = self.__task_queue.get_tasks(None, None)

        for task in tasks:
            self.__table_main.AppendRow(['', task.name(), task.identity(), ''])
            index = self.__table_main.rowCount() - 1

            # Add check box
            check_item = QTableWidgetItem()
            check_item.setCheckState(QtCore.Qt.Unchecked)
            self.__table_main.setItem(index, 0, check_item)

            # Add action button
            button = QPushButton('Cancel')
            button.clicked.connect(partial(self.__on_action_button, task.name(), task.identity()))
            self.__table_main.AddWidgetToCell(index, self.INDEX_ACTION, button)

    # ----------------------------------- Observer -----------------------------------

    def on_task_updated(self, task, change: str):
        self.observe_signal.emit(change)

    # ---------------------------------------------------------------------------------

    def __on_action_button(self, name: str, identity: str):
        if self.__task_queue is not None:
            if identity is not None and identity != '':
                self.__task_queue.cancel_task(identity)
                self.update_table()
            else:
                print('Warning: Task Identity is Empty, will cancel all task.')

    def __on_observe_signal(self, action: str):
        self.update_table()


# ----------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    dlg = WrapperQDialog(TaskQueueUi(None))
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

