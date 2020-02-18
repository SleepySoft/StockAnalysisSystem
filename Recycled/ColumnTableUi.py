#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2019/02/02
@file: ColumnTable.py
@function:
@modify:
"""


from PyQt5.QtWidgets import QLineEdit, QAbstractItemView, QComboBox
from Utiltity.ui_utility import *
from Database.ColumnTable import *


class ColumnTableUi(QWidget):
    def __init__(self, column_table_list: [ColumnTable]):
        super().__init__()

        self.__current_column_table = None

        self.__column_table_list = column_table_list
        self.__translate = QtCore.QCoreApplication.translate

        self.__label_index = QLabel()
        self.__label_column_sel = QLabel()
        self.__line_column_edit = QLineEdit()
        self.__combox_table = QComboBox()
        self.__table_column_index = EasyQTableWidget(0, 2)

        self.__button_add = QPushButton(self.__translate('', '添加列'))
        self.__button_del_column = QPushButton(self.__translate('', '删除列'))
        self.__button_update_column = QPushButton(self.__translate('', '更新列'))

        self.init_ui()

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addLayout(horizon_layout([QLabel(self.__translate('', '选择映射表：')), self.__combox_table]))
        main_layout.addWidget(self.__table_column_index)
        main_layout.addLayout(horizon_layout([QLabel(self.__translate('', '列名：')), self.__label_column_sel,
                                              QLabel(self.__translate('', '序号：')), self.__label_index,
                                              self.__button_del_column]))
        main_layout.addLayout(horizon_layout([QLabel(self.__translate('', '新列名：')),
                                              self.__line_column_edit, self.__button_add, self.__button_update_column]))

    def __config_control(self):
        self.__label_index.setFixedWidth(10)
        self.__label_index.setMinimumWidth(10)
        self.__label_index.setMaximumWidth(10)

        for column_table in self.__column_table_list:
            self.__combox_table.addItem(column_table.GetTableName(), column_table)
        self.__combox_table.currentIndexChanged.connect(self.on_combox_changed)
        self.__combox_table.setEditable(False)
        if len(self.__column_table_list) > 0:
            self.__combox_table.setCurrentIndex(0)
            self.__current_column_table = self.__combox_table.itemData(0)

        self.__table_column_index.setHorizontalHeaderLabels(
            [self.__translate('', '列名'), self.__translate('', '序号')])
        self.__table_column_index.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__table_column_index.setSelectionMode(QAbstractItemView.SingleSelection)
        self.__table_column_index.clicked.connect(self.on_click_table_column_index)

        self.__button_add.clicked.connect(self.on_button_click_add)
        self.__button_del_column.clicked.connect(self.on_button_click_del)
        self.__button_update_column.clicked.connect(self.on_button_click_update)

    def on_combox_changed(self):
        self.__current_column_table = self.__combox_table.currentData()
        self.__update_column_index_table()

    def on_click_table_column_index(self):
        row_content = self.__table_column_index.GetCurrentRow()
        if len(row_content) >= 2:
            self.__label_column_sel.setText(row_content[0])
            self.__label_index.setText(row_content[1])

    def on_button_click_add(self):
        column_name = self.__line_column_edit.text()
        if column_name == '':
            return
        if self.__current_column_table is not None:
            self.__current_column_table.AddColumn(column_name)
            self.__update_column_index_table()

    def on_button_click_del(self):
        column_name = self.__label_column_sel.text()
        if column_name == '':
            return
        if self.__current_column_table is not None:
            self.__current_column_table.DelColumn(column_name)
            self.__update_column_index_table()

    def on_button_click_update(self):
        column_name_old = self.__label_column_sel.text()
        column_name_new = self.__line_column_edit.text()
        if column_name_old == '' or column_name_new == '':
            return
        if self.__current_column_table is not None:
            self.__current_column_table.UpdateColumn(column_name_old, column_name_new)
            self.__update_column_index_table()

    def __update_column_index_table(self):
        self.__table_column_index.setRowCount(0)
        if self.__current_column_table is None:
            return
        column_table = self.__current_column_table.GetColumnNameIndexTable()
        for k, v in sorted(column_table.items(), key=lambda x: x[1]):
            self.__table_column_index.AppendRow([k, str(v)])

    # Interface

    def Init(self):
        self.__update_column_index_table()

