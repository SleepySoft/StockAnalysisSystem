import bisect
import time
import uuid
import threading


class ResourceManager:
    class Resource:
        def __init__(self, res_type: str, res_content: any, expired_time: int):
            self.res_type = res_type
            self.res_data = {}
            self.res_content = res_content
            self.expired_time = expired_time

        def valid(self) -> bool:
            return self.expired_time > time.time()

    def __init__(self):
        self.__resource_table = {}
        self.__next_expired_check = 0
        self.__resource_lock = threading.RLock()

    def get_resource(self, res_id: str) -> Resource or None:
        self.lock()
        self.__check_expired()
        res = self.__resource_table.get(res_id, None)
        self.unlock()
        return res if res is not None and res.valid() else None

    def add_resource(self, res_type: str, res_content: any, expired_time: int) -> str:
        self.lock()
        self.__check_expired()
        res_id = str(uuid.uuid4())
        self.__resource_table[res_id] = ResourceManager.Resource(res_type, res_content, expired_time)
        self.unlock()
        return res_id

    def pop_resource(self, res_id: str) -> Resource or None:
        self.lock()
        self.__check_expired()
        if res_id in self.__resource_table.keys():
            res = self.__resource_table.get(res_id)
            del self.__resource_table[res_id]
        else:
            res = None
        self.unlock()
        return res if res is not None and res.valid() else None

    def set_resource_data(self, res_id: str, k: str, v: any):
        self.lock()
        self.__check_expired()
        res = self.__resource_table.get(res_id)
        if res is not None:
            res.res_data[k] = v
        self.unlock()
        pass

    def get_resource_data(self, res_id: str, k: str) -> any:
        self.lock()
        self.__check_expired()
        res = self.__resource_table.get(res_id)
        if res is not None and res.valid():
            res_data = res.res_data[k]
        else:
            res_data = None
        self.unlock()
        return res_data

    def lock(self):
        self.__resource_lock.acquire()

    def unlock(self):
        self.__resource_lock.release()

    def __check_expired(self):
        now_time = time.time()
        if self.__next_expired_check == 0:
            self.__next_expired_check = now_time
        elif self.__next_expired_check < now_time:
            for k in self.__resource_table.keys():
                v = self.__resource_table.get(k)
                if v.expired_time < now_time:
                    del self.__resource_table[k]
            self.__next_expired_check = now_time + 60













