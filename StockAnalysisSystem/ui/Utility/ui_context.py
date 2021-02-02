from StockAnalysisSystem.core.Utiltity.task_queue import *
from StockAnalysisSystem.interface.interface import SasInterface as sasIF
from StockAnalysisSystem.ui.Utility.resource_sync import ResourceSync


class UiContext:
    def __init__(self):
        self.__sas_interface = None
        self.__ui_task_queue = TaskQueue()
        self.__ui_task_queue.start()
        self.__res_sync = ResourceSync()
        self.__res_sync.start()

    def get_res_sync(self) -> ResourceSync:
        return self.__res_sync

    def get_task_queue(self) -> TaskQueue:
        return self.__ui_task_queue

    def get_sas_interface(self) -> sasIF:
        return self.__sas_interface

    def set_sas_interface(self, sasif: sasIF):
        self.__sas_interface = sasif
        # self.__res_sync.set_sas_interface(sasif)






