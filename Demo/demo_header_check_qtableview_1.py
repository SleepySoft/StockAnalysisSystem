import sys
from PyQt5.QtWidgets import (QApplication, QHeaderView, QStyle, QStyleOptionButton, QTableView)
from PyQt5.QtCore import (pyqtSignal, Qt, QAbstractTableModel, QModelIndex, QRect, QVariant)


# https://wiki.qt.io/Technical_FAQ#How_can_I_insert_a_checkbox_into_the_header_of_my_view.3F
# https://stackoverflow.com/questions/30932528/adding-checkbox-as-vertical-header-in-qtableview
# https://blog.csdn.net/yy123xiang/article/details/78739975

class CheckBoxHeader(QHeaderView):
    clicked = pyqtSignal(bool)

    _x_offset = 3
    _y_offset = 0
    _width = 20
    _height = 20

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super(CheckBoxHeader, self).__init__(orientation, parent)
        self.isOn = False

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        super(CheckBoxHeader, self).paintSection(painter, rect, logicalIndex)
        painter.restore()

        self._y_offset = int((rect.height()-self._width)/2.)

        if logicalIndex == 0:
            option = QStyleOptionButton()
            option.rect = QRect(rect.x() + self._x_offset, rect.y() + self._y_offset, self._width, self._height)
            option.state = QStyle.State_Enabled | QStyle.State_Active
            if self.isOn:
                option.state |= QStyle.State_On
            else:
                option.state |= QStyle.State_Off
            self.style().drawControl(QStyle.CE_CheckBox, option, painter)

    def mousePressEvent(self, event):
        index = self.logicalIndexAt(event.pos())
        if 0 == index:
            x = self.sectionPosition(index)
            if x + self._x_offset < event.pos().x() < x + self._x_offset + self._width and self._y_offset < event.pos().y() < self._y_offset + self._height:
                if self.isOn:
                    self.isOn = False
                else:
                    self.isOn = True
                self.clicked.emit(self.isOn)
                self.update()
        super(CheckBoxHeader, self).mousePressEvent(event)


class MyModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super(MyModel, self).__init__(parent)
        # Keep track of which object are checked
        self.checkList = ['Checked', 'Unchecked']

    def rowCount(self, QModelIndex):
        return len(self.checkList)

    def columnCount(self, QModelIndex):
        return 2

    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return 'Row %d, Column %d' % (row + 1, col + 1)
        elif role == Qt.CheckStateRole:
            if col == 0:
                return Qt.Checked if self.checkList[row] == 'Checked' else Qt.Unchecked
        elif role == Qt.ToolTipRole:
            if col == 0:
                return self.checkList[row]
        return QVariant()

    def setData(self, index, value, role):
        row = index.row()
        col = index.column()
        if role == Qt.CheckStateRole and col == 0:
            self.checkList[row] = 'Checked' if value == Qt.Checked else 'Unchecked'
        return True

    def flags(self, index):
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        return Qt.ItemIsEnabled

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0:
                    return 'Title 1'
                elif section == 1:
                    return 'Title 2'

    def headerClick(self, isOn):
        self.beginResetModel()
        if isOn:
            self.checkList = ['Checked', 'Checked']
        else:
            self.checkList = ['Unchecked', 'Unchecked']
        self.endResetModel()


if __name__ == '__main__':
    a = QApplication(sys.argv)
    tableView = QTableView()
    myModel = MyModel()
    tableView.setModel(myModel)
    header = CheckBoxHeader()
    tableView.setHorizontalHeader(header)
    header.clicked.connect(myModel.headerClick)
    tableView.show()
    a.exec_()


