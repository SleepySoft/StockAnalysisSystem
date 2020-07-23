import os
import errno
from time import sleep
from concurrent import futures

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QTimer, QDateTime, QPoint, pyqtSlot
from PyQt5.QtGui import QColor, QCloseEvent
from PyQt5.QtWidgets import QButtonGroup, QDateTimeEdit, QApplication, QLabel, QTextEdit, QPushButton, QVBoxLayout, \
    QMessageBox, QWidget, QComboBox, QCheckBox, QRadioButton, QLineEdit, QAbstractItemView, QFileDialog, QDialog
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent

from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.ui_utility import *


class WaitingWindow(QDialog):
    WAIT_MODE_NONE = 0
    WAIT_MODE_FUTURE = 1

    def __init__(self):
        super(WaitingWindow, self).__init__()

        self.__finished = False
        self.__freeze_count = 0
        self.__progress: ProgressRate = None
        self.__wait_mode = WaitingWindow.WAIT_MODE_NONE

        # Future
        self.__future: futures.Future = None

        self.__timer = QTimer()
        self.__timer.setInterval(200)
        self.__timer.timeout.connect(self.__on_timer)

        # TODO: Use progress bar
        self.__label_tip_text = QLabel('')
        self.__label_progress = QLabel('')
        self.__button_cancel = QPushButton('Cancel')

        self.__init_ui()

    def __init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addStretch()
        layout.addLayout(horizon_layout([QLabel(''), self.__label_tip_text, QLabel('')], [99, 1, 99]))
        layout.addLayout(horizon_layout([QLabel(''), self.__label_progress, QLabel('')], [99, 1, 99]))
        layout.addLayout(horizon_layout([QLabel(''), self.__button_cancel, QLabel('')], [99, 1, 99]))
        layout.addStretch()

        self.setMinimumSize(400, 250)
        self.setWindowTitle('Progress')
        self.__button_cancel.clicked.connect(self.__on_button_cancel)

    def __on_timer(self):
        done = False
        if self.__wait_mode == WaitingWindow.WAIT_MODE_FUTURE:
            if self.__future is not None:
                done = self.__future.done()
        if self.__progress is not None:
            self.__update_progress()
        else:
            self.__update_animation()
        if done:
            self.__finished = True
            self.close()

    def __on_button_cancel(self):
        self.close()

    def closeEvent(self, event: QCloseEvent):
        self.__timer.stop()
        if not self.__future.done():
            self.__future.cancel()

    def __update_progress(self):
        rate = self.__progress.get_total_progress_rate()
        if abs(rate - 1.0) < 0.00001:
            self.__freeze_count += 1
        else:
            self.__freeze_count = 0

        # If the progress reaches 100% for 2s (200ms * 10) and not quit yet
        # Display animation instead

        if self.__freeze_count < 10:
            self.__label_progress.setText('%.2f%%' % (rate * 100.0))
        else:
            self.__label_progress.setText('')
            self.__update_animation()

    def __update_animation(self):
        text = self.__label_progress.text()
        text = (text + '.') if len(text) < 10 else ''
        self.__label_progress.setText(text)

    # ----------------------------------------------------------------------------------------------

    def set_future_mode(self, tip_text: str, future: futures.Future, progress: ProgressRate):
        self.__future = future
        self.__progress = progress
        self.__label_tip_text.setText(tip_text)
        self.__wait_mode = WaitingWindow.WAIT_MODE_FUTURE
        self.__timer.start()

    # ----------------------------------------------------------------------------------------------

    @staticmethod
    def wait_future(tip_text: str, future: futures, progress: ProgressRate or None = None) -> bool:
        wnd = WaitingWindow()
        wnd.set_future_mode(tip_text, future, progress)
        wnd.exec()
        return wnd.__finished


# ------------------------------------------------ File Entry : main() -------------------------------------------------


def test_task(progress: ProgressRate):
    for i in range(50):
        sleep(0.05)
        progress.increase_progress('000001')
    progress.finish_progress('000001')

    for i in range(100):
        sleep(0.1)
        progress.increase_progress('000002')

    for i in range(10):
        sleep(1)
        progress.set_progress('000003', i, 10)

    sleep(2)
    progress.finish_progress('000004')

    for i in range(100):
        sleep(0.1)
        progress.set_progress('000005', i, 100)


def test_task_wrapper(progress: ProgressRate):
    try:
        test_task(progress)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
    finally:
        pass
    print('Finished')


def main():
    app = QApplication(sys.argv)

    progress = ProgressRate()
    progress.set_progress('000001', 0, 100)
    progress.set_progress('000002', 0, 50)
    progress.set_progress('000003', 0, 10)
    progress.set_progress('000004', 0, 1)
    progress.set_progress('000005', 0, 0)

    with futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(test_task_wrapper, progress)
        if WaitingWindow.wait_future('Waiting Test...', future, progress):
            QMessageBox.information(None, 'Waiting Result', 'Finished')
        else:
            QMessageBox.information(None, 'Waiting Result', 'Canceled')

    exit(app.exec_())


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


















