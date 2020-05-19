from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QComboBox


class SecuritiesSelector(QComboBox):
    def __init__(self, data_utility, parent=None):
        super(SecuritiesSelector, self).__init__(parent)

        self.__data_utility = data_utility

        self.__timer = QTimer()
        self.__timer.setInterval(1000)
        self.__timer.timeout.connect(self.on_timer)

        if self.__data_utility is not None:
            # Timer for update stock list
            self.__timer.start()
        self.setEditable(True)

    def on_timer(self):
        # Check stock list ready and update combobox
        if self.__data_utility.stock_cache_ready():
            stock_list = self.__data_utility.get_stock_list()
            for stock_identity, stock_name in stock_list:
                self.addItem(stock_identity + ' | ' + stock_name, stock_identity)
            self.__timer.stop()

    def get_input_securities(self) -> str:
        input_securities = self.currentText()
        if '|' in input_securities:
            input_securities = input_securities.split('|')[0].strip()
        return input_securities


