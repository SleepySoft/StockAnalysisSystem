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
from PyQt5.QtWidgets import QLineEdit, QAbstractItemView, QFileDialog, QCheckBox

from Utiltity.ui_utility import *
from Database.AliasTable import *


class AliasTableUi(QWidget):
    def __init__(self, alias_table: AliasTable):
        super().__init__()

        self.__has_update = False
        self.__sel_std_name = ''
        self.__sel_alias = ''
        self.__only_show_no_alias = False

        self.__alias_table = alias_table
        self.__translate = QtCore.QCoreApplication.translate

        self.__table_alias = EasyQTableWidget(0, 1)
        self.__table_standard_name = EasyQTableWidget(0, 3)

        self.__check_only_no_alias = QCheckBox(self.__translate('', '只看无别名'))

        self.__button_collect = QPushButton(self.__translate('', '采集现用名'))
        self.__button_load_csv = QPushButton(self.__translate('', '载入CSV'))
        self.__button_manual_save = QPushButton(self.__translate('', '手动保存'))
        self.__button_del_standard = QPushButton(self.__translate('', '删除记录'))

        self.__label_standard = QLabel()
        self.__line_standard_edit = QLineEdit()
        self.__button_update_standard_name = QPushButton(self.__translate('', '更改标准名'))

        self.__label_alias = QLabel()
        self.__line_alias = QLineEdit()
        self.__button_add_alias = QPushButton(self.__translate('', '添加别名'))
        self.__button_del_alias = QPushButton(self.__translate('', '删除别名'))

        self.init_ui()

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.__table_standard_name)
        left_layout.addLayout(horizon_layout([
            self.__button_collect,
            self.__button_load_csv,
            self.__check_only_no_alias,
            self.__button_manual_save,
            self.__button_del_standard]))

        right_layout = QVBoxLayout()
        right_layout.addLayout(horizon_layout([QLabel(self.__translate('', '当前标准名：')),
                                               self.__label_standard]))
        right_layout.addLayout(horizon_layout([self.__button_update_standard_name,
                                               QLabel(self.__translate('', ' -> ')),
                                               self.__line_standard_edit]))
        right_layout.addWidget(self.__table_alias)
        right_layout.addLayout(horizon_layout([QLabel(self.__translate('', '当前别名：')),
                                               self.__label_alias,
                                               self.__button_del_alias]))
        right_layout.addLayout(horizon_layout([QLabel(self.__translate('', '添加别名：')),
                                              self.__line_alias, self.__button_add_alias]))

        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

    def __config_control(self):
        self.__table_alias.setHorizontalHeaderLabels(
            [self.__translate('', '别名')])
        self.__table_alias.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__table_alias.setSelectionMode(QAbstractItemView.SingleSelection)

        self.__table_standard_name.setHorizontalHeaderLabels(
            [self.__translate('', '标准名'), self.__translate('', '别名'), self.__translate('', '别名数量')])
        self.__table_standard_name.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__table_standard_name.setSelectionMode(QAbstractItemView.SingleSelection)

        self.__table_alias.clicked.connect(self.on_click_table_alias)
        self.__table_standard_name.clicked.connect(self.on_click_table_standard_name)

        self.__button_collect.clicked.connect(self.on_button_click_refresh)
        self.__button_load_csv.clicked.connect(self.on_button_click_load_csv)
        self.__check_only_no_alias.clicked.connect(self.on_check_click_only_no_alias)
        self.__button_manual_save.clicked.connect(self.on_button_click_manual_save)
        self.__button_del_standard.clicked.connect(self.on_button_click_del_standard)

        self.__button_update_standard_name.clicked.connect(self.on_button_click_update_standard)
        self.__button_add_alias.clicked.connect(self.on_button_click_add_alias)
        self.__button_del_alias.clicked.connect(self.on_button_click_del_alias)

    # ---------------------------------------------------- Interface ---------------------------------------------------

    def get_select_standard_name(self):
        return self.__sel_std_name

    # ---------------------------------------------------- UI Event ----------------------------------------------------

    def on_click_table_alias(self):
        row_content = self.__table_alias.GetCurrentRow()
        if len(row_content) >= 1:
            self.__sel_alias = row_content[0]
            self.__label_alias.setText(self.__sel_alias)

    def on_click_table_standard_name(self):
        standard_name = self.__table_standard_name.GetCurrentRow()
        if len(standard_name) >= 1:
            self.__sel_std_name = standard_name[0]
            self.__label_standard.setText(self.__sel_std_name)
            self.__update_alias_table()

    def on_button_click_refresh(self):
        self.__alias_table.collect_names()
        self.__update_standard_table()

    def on_button_click_load_csv(self):
        file_path, ok = QFileDialog.getOpenFileName(self, 'Load CSV file', '', 'CSV Files (*.csv);;All Files (*)')
        if ok:
            self.__alias_table.load_from_csv(file_path)
            self.__update_standard_table()
            self.__has_update = True

    def on_check_click_only_no_alias(self):
        self.__only_show_no_alias = self.__check_only_no_alias.isChecked()
        self.__update_standard_table()

    def on_button_click_manual_save(self):
        if self.__alias_table.dump_to_db():
            QMessageBox.information(self,
                                    self.__translate('', '提示'),
                                    self.__translate('', '保存到数据库成功'), QMessageBox.Ok)
            self.__has_update = False

    def on_button_click_del_standard(self):
        select_model = self.__table_standard_name.selectionModel()
        if not select_model.hasSelection():
            return
        row_index = select_model.currentIndex().row()
        standard = self.__table_standard_name.model().index(row_index, 0).data()
        self.__alias_table.del_standard_name(standard)
        # self.__alias_table.dump_to_db()
        self.__has_update = True
        self.__update_alias_table()
        self.__update_standard_table()

    def on_button_click_update_standard(self):
        standard_old = self.get_select_standard_name()
        standard_new = self.__line_standard_edit.text()

        if standard_old == '' or standard_new == '':
            return

        # select_model = self.__table_standard_name.selectionModel()
        # if not select_model.hasSelection():
        #     return
        # row_index = select_model.currentIndex().row()
        # standard = self.__table_standard_name.model().index(row_index, 0).data()

        reply = QMessageBox.information(self, self.__translate('', '警告'),
                                        self.__translate('',
                                                         '更改标准名会影响所有使用这个字段名的表，' +
                                                         '操作即时生效且无法回滚。\n是否确定？'),
                                        QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        self.__alias_table.update_standard_name(standard_old, standard_new)
        # self.__alias_table.dump_to_db()
        self.__has_update = True
        self.__update_alias_table()
        self.__update_standard_table()

    def on_button_click_add_alias(self):
        alias = self.__line_alias.text()
        standard = self.__label_standard.text()
        self.__alias_table.add_alias(alias, standard)
        # self.__alias_table.dump_to_db()
        self.__has_update = True
        self.__update_alias_table()
        self.__update_standard_table()

    def on_button_click_del_alias(self):
        if self.__sel_alias != '':
            self.__alias_table.del_alias(self.__sel_alias)
            self.__sel_alias = ''
            self.__label_alias.setText('')
            # self.__alias_table.dump_to_db()
            self.__has_update = True
            self.__update_alias_table()
            self.__update_standard_table()

    # ---------------------------------------------------- Private -----------------------------------------------------

    def __update_alias_table(self):
        sel_std_name = self.get_select_standard_name()
        aliases_standard_table = self.__alias_table.get_alias_standard_table()
        self.__table_alias.setRowCount(0)
        for alias in sorted(aliases_standard_table.keys()):
            standard_name = aliases_standard_table[alias]
            if standard_name == sel_std_name:
                row_count = self.__table_alias.rowCount()
                self.__table_alias.insertRow(row_count)
                self.__table_alias.setItem(row_count, 0, QTableWidgetItem(alias))
                self.__label_standard.setText('<empty>' if standard_name == '' else standard_name)
                # self.__table_alias.setItem(row_count, 1, QTableWidgetItem(standard_name))

    def __update_standard_table(self):
        standard_name_list = self.__alias_table.get_standard_name_list()
        aliases_standard_table = self.__alias_table.get_alias_standard_table()

        self.__table_standard_name.setRowCount(0)
        for standard_name in standard_name_list:
            if standard_name.strip() == '':
                continue
            alias_list = self.__get_alias_list(aliases_standard_table, standard_name)
            if self.__only_show_no_alias and len(alias_list) != 0:
                continue
            row_count = self.__table_standard_name.rowCount()
            self.__table_standard_name.insertRow(row_count)
            self.__table_standard_name.setItem(row_count, 0, QTableWidgetItem(standard_name))
            self.__table_standard_name.setItem(row_count, 1, QTableWidgetItem(','.join(alias_list)))
            self.__table_standard_name.setItem(row_count, 2, QTableWidgetItem(str(len(alias_list))))

    def __get_alias_list(self, aliases_standard_table: dict, alias: str) -> int:
        alias_list = []
        for key in aliases_standard_table:
            if aliases_standard_table[key] == alias:
                alias_list.append(key)
        return alias_list

    # Interface

    def Init(self):
        # self.__update_alias_table()
        self.__update_standard_table()



