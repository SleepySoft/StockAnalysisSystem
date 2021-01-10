import threading
import time

from StockAnalysisSystem.interface.interface import SasInterface as sasIF


class ResourceSync(threading.Thread):
    def __init__(self):
        self.__quit = False
        self.__sasif = None
        self.__sync_table = {}
        self.__resource_table = {}
        self.__lock = threading.Lock()
        super(ResourceSync, self).__init__()

    def set_sas_interface(self, sasif: sasIF):
        self.__sasif = sasif

    def run(self):
        while not self.__quit:
            self.sync_resource()
            time.sleep(0.5)

    def stop(self):
        self.__quit = True

    def sync_resource(self):
        with self.__lock:
            if self.__sasif is None:
                return
            sasif = self.__sasif

        self.__lock.acquire()
        sync_table = self.__sync_table.copy()
        self.__lock.release()

        res_table = {}
        for res_id in sync_table.keys():
            keys = sync_table[res_id]
            res = sasif.sas_get_resource(res_id, keys)
            if len(keys) == len(res):
                res_table[res_id] = {k: v for k, v in zip(keys, res)}

        self.__lock.acquire()
        self.__resource_table = res_table
        self.__lock.release()

    def get_resource(self, res_id: str, k: str) -> any:
        with self.__lock:
            res = self.__resource_table.get(res_id)
            return res.get(k, None) if res is not None else None

    def add_sync_resource(self, res_id: str, keys: [str]):
        if not isinstance(keys, (list, tuple, set)):
            keys = [keys]
        else:
            keys = list(keys)
        self.__lock.acquire()
        if res_id not in self.__sync_table.keys():
            self.__sync_table[res_id] = keys
        else:
            self.__sync_table[res_id] = list(set(self.__sync_table[res_id].extend(keys)))
        self.__lock.release()

    def remove_sync_resource(self, res_id: str or list or tuple):
        if isinstance(res_id, str):
            res_id = [res_id]
        self.__lock.acquire()
        for res in res_id:
            if res in self.__sync_table.keys():
                del self.__sync_table[res]
            if res in self.__resource_table.keys():
                del self.__resource_table[res]
        self.__lock.release()





