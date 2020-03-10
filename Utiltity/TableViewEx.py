import datetime
import logging
import sys
import traceback
from functools import partial

from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import (pyqtSignal, Qt, QRect, QTimer)
from PyQt5.QtWidgets import (QApplication, QHeaderView, QStyle, QStyleOptionButton, QTableView, QHBoxLayout, QWidget,
                             QPushButton)


# ----------------------------------------------------------------------------------------------------------------------
#                                                     TableViewEx
# ----------------------------------------------------------------------------------------------------------------------

# ------------------------------------ CheckBoxHeader ------------------------------------
# -------------------- https://stackoverflow.com/a/30934160/12929244 ---------------------
# ----------------------------------------------------------------------------------------

class CheckBoxHeader(QHeaderView):
    clicked = pyqtSignal(int, bool)

    _x_offset = 3
    _y_offset = 0   # This value is calculated later, based on the height of the paint rect
    _width = 20
    _height = 20

    def __init__(self, column_indices, orientation=Qt.Horizontal, parent=None):
        super(CheckBoxHeader, self).__init__(orientation, parent)
        self.setSectionResizeMode(QHeaderView.Stretch)
        self.setSectionsClickable(True)

        if isinstance(column_indices, list) or isinstance(column_indices, tuple):
            self.column_indices = column_indices
        elif isinstance(column_indices, int):
            self.column_indices = [column_indices]
        else:
            raise RuntimeError('column_indices must be a list, tuple or integer')

        self.isChecked = {}
        for column in self.column_indices:
            self.isChecked[column] = 0

    def setCheckableColumn(self, col: int):
        if col not in self.column_indices:
            self.column_indices.append(col)
            self.isChecked[col] = 0

    def isColumnCheckable(self, col: int) -> bool:
        return col in self.column_indices

    def paintSection(self, painter, rect, logical_index):
        painter.save()
        super(CheckBoxHeader, self).paintSection(painter, rect, logical_index)
        painter.restore()

        #
        self._y_offset = int((rect.height() - self._width)/2.)

        if logical_index in self.column_indices:
            option = QStyleOptionButton()
            option.rect = QRect(rect.x() + self._x_offset, rect.y() + self._y_offset, self._width, self._height)
            option.state = QStyle.State_Enabled | QStyle.State_Active
            if self.isChecked[logical_index] == 2:
                option.state |= QStyle.State_NoChange
            elif self.isChecked[logical_index]:
                option.state |= QStyle.State_On
            else:
                option.state |= QStyle.State_Off

            self.style().drawControl(QStyle.CE_CheckBox,option,painter)

    def updateCheckState(self, index, state):
        self.isChecked[index] = state
        self.viewport().update()

    def mousePressEvent(self, event):
        index = self.logicalIndexAt(event.pos())
        if 0 <= index < self.count():
            x = self.sectionPosition(index)
            if x + self._x_offset < event.pos().x() < x + self._x_offset + self._width and self._y_offset < event.pos().y() < self._y_offset + self._height:
                if self.isChecked[index] == 1:
                    self.isChecked[index] = 0
                else:
                    self.isChecked[index] = 1

                self.clicked.emit(index, self.isChecked[index])
                self.viewport().update()
            else:
                super(CheckBoxHeader, self).mousePressEvent(event)
        else:
            super(CheckBoxHeader, self).mousePressEvent(event)


# ----------------------------- TableViewExModel -----------------------------

class TableViewExModel(QStandardItemModel):
    def __init__(self, header: CheckBoxHeader):
        super(TableViewExModel, self).__init__()
        self.__header = header
        self.__header.clicked.connect(self.batch_set_check)
        self.itemChanged.connect(self.__on_item_changed)

    def batch_set_check(self, index, state):
        for i in range(self.rowCount()):
            item = self.item(i, index)
            item.setCheckState(Qt.Checked if state else Qt.Unchecked)

    def __on_item_changed(self):
        for i in range(self.columnCount()):
            checked = 0
            unchecked = 0
            for j in range(self.rowCount()):
                item = self.item(j, i)
                if item is None:
                    continue
                if self.item(j, i).checkState() == Qt.Checked:
                    checked += 1
                elif self.item(j, i).checkState() == Qt.Unchecked:
                    unchecked += 1

            if checked and unchecked:
                self.__header.updateCheckState(i, 2)
            elif checked:
                self.__header.updateCheckState(i, 1)
            else:
                self.__header.updateCheckState(i, 0)


# ------------------------------ QTableViewEx ------------------------------

class TableViewEx(QTableView):
    def __init__(self, *__args):
        super(TableViewEx, self).__init__(*__args)
        self.__header = CheckBoxHeader([], parent=self)
        self.__model = TableViewExModel(self.__header)
        self.setModel(self.__model)
        self.setHorizontalHeader(self.__header)

    def Clear(self):
        self.__model.clear()

    # -------------------------- Row / Column --------------------------

    def RowCount(self) -> int:
        return self.__model.rowCount()

    def ColumnCount(self) -> int:
        return self.__model.columnCount()

    def SetRowCount(self, count: int):
        return self.__model.setRowCount(count)

    def SetColumnCount(self, count: int):
        return self.__model.setColumnCount(count)

    def SetColumn(self, columns: [str]):
        self.__model.setHorizontalHeaderLabels(columns)

    def AppendRow(self, texts: [str]):
        row = []
        if not isinstance(texts, (list, tuple)):
            texts = [texts]
        for col in range(len(texts)):
            item = QStandardItem(str(texts[col]))
            item.setCheckable(self.__header.isColumnCheckable(col))
            row.append(item)
        self.__model.appendRow(row)

    def AppendColumn(self, title: str):
        item = QStandardItem(title)
        self.__model.appendColumn(item)

    # ------------------------------ Items ------------------------------

    # ------------------------ Gets ------------------------

    def GetItem(self, row: int, col: int) -> QStandardItem:
        return self.__model.item(row, col)

    def GetItemText(self, row: int, col: int) -> str:
        item = self.GetItem(row, col)
        return item.text() if item is not None else ''

    def GetItemData(self, row: int, col: int) -> any:
        item = self.GetItem(row, col)
        return item.data(Qt.UserRole) if item is not None else ''

    def GetItemCheckState(self, row: int, col: int) -> int:
        item = self.GetItem(row, col)
        return item.checkState() if item is not None else Qt.Unchecked

    # ------------------------ Sets ------------------------

    def SetItemText(self, row: int, col: int, text: str):
        item = self.GetItem(row, col)
        if item is not None:
            item.setText(text)

    def SetItemData(self, row: int, col: int, data: any):
        item = self.GetItem(row, col)
        if item is not None:
            item.setData(data, Qt.UserRole)

    def SetItemCheckState(self, row: int, col: int, state: int):
        if state in [Qt.Checked, Qt.Unchecked,  Qt.PartiallyChecked]:
            item = self.GetItem(row, col)
            if item is not None:
                item.setCheckState(state)
        else:
            print('Check state should be one of [Qt.Checked, Qt.Unchecked,  Qt.PartiallyChecked]')

    # ----------------------------- Widgets -----------------------------

    def SetCellWidget(self, row: int, col: int, widgets: [QWidget]):
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        wrap_widget = QWidget()
        wrap_widget.setLayout(layout)
        wrap_widget.setContentsMargins(0, 0, 0, 0)
        if not isinstance(widgets, (list, tuple)):
            widgets = [widgets]
        for widget in widgets:
            layout.addWidget(widget)
        item = self.GetItem(row, col)
        if item is not None:
            self.setIndexWidget(item.index(), wrap_widget)

    # ------------------------------ Config ------------------------------

    def SetCheckableColumn(self, col: int):
        self.__header.setCheckableColumn(col)

    # ------------------------------ Select ------------------------------

    def GetCurrentRow(self) -> int:
        return self.selectionModel().currentIndex().row() if self.selectionModel().hasSelection() else -1

    def GetSelectRows(self) -> [int]:
        indexes = self.selectedIndexes()
        return [index.row() for index in indexes]


# ----------------------------------------------------------------------------------------------------------------------

def on_timer(table: TableViewEx):
    table.SetItemText(0, 3, str(datetime.datetime.now()))


def main():
    app = QApplication(sys.argv)

    columns = ['Column1', 'Column2', 'Column3', 'Column4', 'Column5']

    table = TableViewEx()
    table.SetColumn(columns)
    table.SetCheckableColumn(0)
    table.setSortingEnabled(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    timer = QTimer()
    timer.setInterval(1000)
    timer.timeout.connect(partial(on_timer, table))
    timer.start()

    for row in range(10):
        row_items = []
        for col in range(len(columns)):
            row_items.append('Item %s,%s' % (row, col))
        table.AppendRow(row_items)
        table.SetCellWidget(row, 4, QPushButton('Push'))
    table.show()

    timer = QTimer()
    timer.setInterval(1000)
    timer.timeout.connect(partial(on_timer, table))
    timer.start()

    sys.exit(app.exec_())


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
    logging.basicConfig(level='INFO')
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass

