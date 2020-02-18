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

from Utiltity.common import *
from Utiltity.ui_utility import *
from Database.UpdateTableEx import *


class UpdateAgent:
    def __init__(self):
        pass

    def group(self) -> str:
        """
        Get the group name of update content. It's used for tab classification.
        :return: The name of group.
        """
        nop(self)
        return ''

    def items(self) -> [(str, str)]:
        """
        Get the update items. The item should include following information:
            Index   Information
            0       The readable name of this item.
            1       The identification (tags) of this item.
        :return: The list of items' information.
        """
        nop(self)
        return []

    def reset_items(self, items: str or [str]) -> bool:
        """
        Reset and clear items and its update record.
        :param items: The identification of items that needs clear
        :return: true if clear is done else false
        """
        nop(self)
        return True

    def update_items(self, items: str or [str], force: bool) -> bool:
        """
        Update specified items. The identification of items should come from items() function.
        :param items: The identification of items that needs update.
        :param force: If true, force update to recent data. Else depends on its update strategy.
        :return: true if update is done else false
        """
        nop(self)
        nop(items)
        nop(force)
        return True


class UpdateTableExUi(QWidget):
    def __init__(self, update_table: UpdateTableEx):
        super(UpdateTableExUi, self).__init__(None)

        self.__update_table = update_table
        self.__update_agents = []

        self.__ui_inited = False

    def init_ui(self):
        pass

    def update_ui(self):
        if not self.__ui_inited:
            return

    def get_update_table(self) -> UpdateTableEx:
        return self.__update_table

    def register_update_agent(self, agent: UpdateAgent):
        if agent not in self.__update_agents:
            self.__update_agents.append(agent)
        self.update_ui()





















