import bisect
import time
import uuid
import threading


class ResourceManager:
    RESOURCE_MASTER = 'master'
    RESOURCE_RESULT = 'result'
    RESOURCE_STATUS = 'status'
    RESOURCE_PROGRESS = 'progress'

    class Resource:
        def __init__(self, res_type: str, expired_time: int, **res_data):
            self.res_type = res_type
            self.res_data = res_data
            self.res_tags = []
            self.expired_time = expired_time

        def type(self):
            return self.res_type

        def keys(self) -> list:
            return list(self.res_data)

        def data(self, key: str) -> any:
            return self.res_data.get(key, None)

        def update(self, key: str, res: any):
            self.res_data[key] = res

        def delete(self, key: str):
            if key in self.res_data.keys():
                del self.res_data[key]

        def valid(self) -> bool:
            return self.expired_time > time.time()

        def renew(self, sec: int):
            self.expired_time += sec

        def get_tags(self) -> [str]:
            return self.res_tags

        def set_tags(self, tags: [str]):
            self.res_tags = tags

    def __init__(self):
        self.__resource_table = {}
        self.__next_expired_check = 0
        self.__resource_lock = threading.RLock()

    def allocate_resource(self, res_type: str, expired_time: int = time.time() + 3600, **kwargs) -> str:
        with self.__resource_lock:
            self.__check_expired()
            res_id = str(uuid.uuid4())
            self.__resource_table[res_id] = ResourceManager.Resource(res_type, expired_time, **kwargs)
            return res_id

    def pop_resource(self, res_id: str) -> Resource or None:
        with self.__resource_lock:
            self.__check_expired()
            if res_id in self.__resource_table.keys():
                res = self.__resource_table.get(res_id)
                del self.__resource_table[res_id]
            else:
                res = None
            return res

    def set_resource(self, res_id: str, k: str, v: any):
        with self.__resource_lock:
            res: ResourceManager.Resource = self.__get_resource(res_id)
            if res is not None:
                res.update(k, v)

    def get_resource(self, res_id: str, k: str) -> any:
        with self.__resource_lock:
            res: ResourceManager.Resource = self.__get_resource(res_id)
            return res.data(k) if res is not None else None

    def set_resource_tags(self, res_id: str, tags: [str]):
        with self.__resource_lock:
            res: ResourceManager.Resource = self.__get_resource(res_id)
            if res is not None:
                res.set_tags(tags)

    def get_resource_tags(self, res_id: str) -> [str]:
        with self.__resource_lock:
            res: ResourceManager.Resource = self.__get_resource(res_id)
            return res.get_tags() if res is not None else []

    def find_resource_by_tags(self, tags: [str]) -> [str]:
        res_id = []
        tags = set(tags)
        with self.__resource_lock:
            for _id, res in self.__resource_table.items():
                if len(set(res.get_tags()) & tags) == len(tags):
                    res_id.append(_id)
        return tags


    # ----------------------------------------------------------

    @staticmethod
    def __now() -> int:
        return int(time.time())

    def __check_expired(self):
        now_time = self.__now()
        if self.__next_expired_check == 0:
            self.__next_expired_check = now_time
        elif self.__next_expired_check < now_time:
            for k in self.__resource_table.keys():
                v = self.__resource_table.get(k)
                if v.expired_time < now_time:
                    del self.__resource_table[k]
            self.__next_expired_check = now_time + 10

    def __get_resource(self, res_id: str) -> Resource or None:
        self.__check_expired()
        return self.__resource_table.get(res_id, None)














