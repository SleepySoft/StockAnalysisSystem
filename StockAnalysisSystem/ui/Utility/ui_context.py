from StockAnalysisSystem.core.Utiltity.task_queue import *
from StockAnalysisSystem.interface.interface import SasInterface as sasIF


class UiContext:
    def __init__(self):
        self.__sas_interface = None
        self.__ui_task_queue = TaskQueue()
        self.__ui_task_queue.start()

    def get_task_queue(self) -> TaskQueue:
        return self.__ui_task_queue

    def get_sas_interface(self) -> sasIF:
        return self.__sas_interface

    def set_sas_interface(self, sasif: sasIF):
        self.__sas_interface = sasif






