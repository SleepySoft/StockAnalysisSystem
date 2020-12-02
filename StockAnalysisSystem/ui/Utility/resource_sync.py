import threading
from StockAnalysisSystem.interface.interface import SasInterface as sasIF


class ResourceSync:
    def __init__(self, sasif: sasIF):
        self.__sasif = sasif
        self.__sync_res = []
        self.__res_table = {}
        self.__lock = threading.Lock()

    def sync_resource(self):
        self.__lock.acquire()
        sync_res = self.__sync_res.copy()
        self.__lock.release()

        res_table = {}
        for res_id in sync_res:
            res = self.__sasif.sas_get_resource(res_id)
            res_table = res

        self.__lock.acquire()
        self.__res_table = res_table
        self.__lock.release()

    def get_resource(self, res_id: str) -> any:
        self.__lock.acquire()
        res = self.__res_table.get(res_id, None)
        self.__lock.release()
        return res

    def add_sync_resource(self, res_id: str):
        self.__lock.acquire()
        self.__sync_res.append(res_id)
        self.__lock.release()

    def remove_sync_resource(self, res_id: str or list or tuple):
        if isinstance(res_id, str):
            res_id = [res_id]
        self.__lock.acquire()
        self.__sync_res = list(set(self.__sync_res).difference(set(res_id)))
        self.__lock.release()





