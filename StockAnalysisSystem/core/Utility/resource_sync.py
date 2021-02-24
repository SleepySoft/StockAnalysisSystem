import threading
import time

from StockAnalysisSystem.core.Utility.task_queue import TaskQueue
from StockAnalysisSystem.interface.interface import SasInterface as sasIF


# --------------------------------------------------- ResourceUpdater --------------------------------------------------

class ResourceUpdater:
    def __init__(self, sasif: sasIF, identity: str):
        self.__sasif = sasif
        self.__identity = identity
        self.__quit = False
        self.__res_table = {}
        self.__lock = threading.Lock()

    # -------------------------------------- Override -------------------------------------

    def update(self):
        pass

    # ---------------------------------- Common Functions ----------------------------------

    def lock(self):
        self.__lock.acquire()

    def unlock(self):
        self.__lock.release()

    def identity(self) -> str:
        return self.__identity

    def interrupt(self):
        self.__quit = True

    def get_sas_interface(self) -> sasIF:
        return self.__sasif

    def update_resource(self, update_table: [(str, [str])]) -> dict:
        """
        Update the resource specified by update_table
        :param update_table:
                                [
                                    (res_id1, [key1, key2, key3, ...])
                                    (res_id2, [key1, key2, key3, ...]),
                                     ...
                                ]
        :return: Resource table
                                {
                                    res_id1: {key1: value1, key2: value2, key3: value3, ......},
                                    res_id2: {key1: value1, key2: value2, key3: value3, ......},
                                    ...
                                }
        """
        res_table = self.__sasif.sas_get_resource(update_table)
        return res_table

    def get_resource(self, res_id: str, key: str) -> any:
        with self.__lock:
            res = self.__res_table.get(res_id)
            return res.get(key, None) if res is not None else None

    def set_resource_table(self, res_table: dict):
        if isinstance(res_table, dict):
            with self.__lock:
                self.__res_table = res_table


# ------------------------------------------- Res ID Updater -------------------------------------------

class ResourceIdUpdater(ResourceUpdater):
    def __init__(self, sasif: sasIF, identity: str):
        self.__sync_table = {}
        super(ResourceIdUpdater, self).__init__(sasif, identity)

    # ------------------- Override -------------------

    def update(self):
        self.lock()
        update_table = [(res_id, res_keys) for res_id, res_keys in self.__sync_table.items()]
        self.unlock()
        res_table = self.update_resource(update_table)
        self.set_resource_table(res_table)

    # ---------------- Extra Function ----------------

    def add_sync_resource(self, res_id: str, keys: [str]):
        if not isinstance(keys, (list, tuple, set)):
            keys = [keys]
        else:
            keys = list(keys)
        self.lock()
        if res_id not in self.__sync_table.keys():
            self.__sync_table[res_id] = keys
        else:
            self.__sync_table[res_id] = list(set(self.__sync_table[res_id].extend(keys)))
        self.unlock()

    def remove_sync_resource(self, res_id: str or list or tuple):
        if isinstance(res_id, str):
            res_id = [res_id]
        self.lock()
        for res in res_id:
            if res in self.__sync_table.keys():
                del self.__sync_table[res]
        self.unlock()


# ------------------------------------------- Res Tag Updater -------------------------------------------

class ResourceTagUpdater(ResourceUpdater):
    def __init__(self, sasif: sasIF, identity: str):
        self.__sync_tags = []
        self.__sync_keys = []
        self.__res_ids = []
        super(ResourceTagUpdater, self).__init__(sasif, identity)

    # ------------------- Override -------------------

    def update(self):
        self.lock()
        tags = self.__sync_tags
        self.unlock()

        if len(tags) > 0:
            res_ids = self.get_sas_interface().sas_find_resource(tags)

            self.lock()
            self.__res_ids = res_ids
            update_table = [(res_id, self.__sync_keys) for res_id in res_ids]
            self.unlock()

            res_table = self.update_resource(update_table)
            self.set_resource_table(res_table)

    # ---------------- Extra Function ----------------

    def get_resource_ids(self) -> [str]:
        return self.__res_ids

    def add_resource_tags(self, tags: [str]):
        tags = list(tags) if isinstance(tags, (list, tuple, set)) else [str(tags)]
        self.lock()
        self.__sync_tags.extend(tags)
        self.__sync_tags = list(set(self.__sync_tags))
        self.unlock()

    def set_resource_tags(self, tags: [str]):
        tags = list(tags) if isinstance(tags, (list, tuple, set)) else [str(tags)]
        self.lock()
        self.__sync_tags = tags
        self.unlock()

    def set_update_resource_keys(self, keys: [str]):
        self.lock()
        self.__sync_keys = list(keys) if isinstance(keys, (list, tuple, set)) else [str(keys)]
        self.unlock()


# ------------------------------------------- Res Update Task -------------------------------------------

class ResourceUpdateTask(TaskQueue.Task):
    def __init__(self, res_updater: ResourceUpdater):
        self.__res_updater = res_updater
        super(ResourceUpdateTask, self).__init__('ResourceUpdateTask')

    # ------------------- Override -------------------

    def run(self):
        self.__res_updater.update()

    def quit(self):
        self.__res_updater.interrupt()

    def identity(self) -> str:
        return self.__res_updater.identity()

    # ---------------- Extra Function ----------------

    def get_updater(self) -> ResourceUpdater:
        return self.__res_updater


# ---------------------------------------------------- ResourceSync ----------------------------------------------------

# Kind of stupid, deprecated.

# class ResourceSync(threading.Thread):
#     def __init__(self):
#         self.__quit = False
#         self.__updater_table = {}
#         self.__lock = threading.Lock()
#         super(ResourceSync, self).__init__()
#
#     def run(self):
#         while not self.__quit:
#             self.sync_resource()
#             time.sleep(1)
#
#     def stop(self):
#         self.__quit = True
#
#     def sync_resource(self):
#         with self.__lock:
#             updater_table = self.__updater_table
#
#         for _id in updater_table.keys():
#             updater: ResourceUpdater = updater_table[_id]
#             updater.update()
#
#     def get_resource(self, res_id: str, key: str) -> any:
#         with self.__lock:
#             for _id in self.__updater_table.keys():
#                 updater: ResourceUpdater = self.__updater_table[_id]
#                 res = updater.get_resource(res_id, key)
#                 if res is not None:
#                     return res
#         return None
#
#     def add_sync_resource(self, updater: ResourceIdUpdater):
#         with self.__lock:
#             self.__updater_table[updater.identity()] = updater
#
#     def remove_sync_resource(self, updater_id: str):
#         with self.__lock:
#             if updater_id in self.__updater_table:
#                 del self.__updater_table[updater_id]





