import sys
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import (pyqtSignal, Qt, QAbstractTableModel, QModelIndex, QRect, QVariant)
from PyQt5.QtWidgets import (QApplication, QHeaderView, QStyle, QStyleOptionButton, QTableView)


# A Header supporting checkboxes to the left of the text of a subset of columns
# The subset of columns is specified by a list of column_indices at
# instantiation time
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

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        super(CheckBoxHeader, self).paintSection(painter, rect, logicalIndex)
        painter.restore()

        #
        self._y_offset = int((rect.height()-self._width)/2.)

        if logicalIndex in self.column_indices:
            option = QStyleOptionButton()
            option.rect = QRect(rect.x() + self._x_offset, rect.y() + self._y_offset, self._width, self._height)
            option.state = QStyle.State_Enabled | QStyle.State_Active
            if self.isChecked[logicalIndex] == 2:
                option.state |= QStyle.State_NoChange
            elif self.isChecked[logicalIndex]:
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


if __name__=='__main__':

    def updateModel(index, state):
        for i in range(model.rowCount()):
            item = model.item(i, index)
            item.setCheckState(Qt.Checked if state else Qt.Unchecked)

    def modelChanged():
        for i in range(model.columnCount()):
            checked = 0
            unchecked = 0
            for j in range(model.rowCount()):
                if model.item(j,i).checkState() == Qt.Checked:
                    checked += 1
                elif model.item(j,i).checkState() == Qt.Unchecked:
                    unchecked += 1

            if checked and unchecked:
                header.updateCheckState(i, 2)
            elif checked:
                header.updateCheckState(i, 1)
            else:
                header.updateCheckState(i, 0)

    app = QApplication(sys.argv)

    tableView = QTableView()
    model = QStandardItemModel()
    model.itemChanged.connect(modelChanged)
    model.setHorizontalHeaderLabels(['Title 1\nA Second Line','Title 2'])
    header = CheckBoxHeader([0,1], parent = tableView)
    header.clicked.connect(updateModel)

    # populate the models with some items
    for i in range(3):
        item1 = QStandardItem('Item %d'%i)
        item1.setCheckable(True)

        item2 = QStandardItem('Another Checkbox %d' % i)
        item2.setCheckable(True)

        model.appendRow([item1, item2])

    tableView.setModel(model)
    tableView.setHorizontalHeader(header)
    tableView.setSortingEnabled(True)
    tableView.show()

    sys.exit(app.exec_())





