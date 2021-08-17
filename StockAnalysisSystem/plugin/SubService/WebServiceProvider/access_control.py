import functools
import threading


# --------------------------------------------------------------------------------

class AccessData:
    ACCESS_MODE_ALL = -1
    ACCESS_MODE_NONE = 0
    ACCESS_MODE_WHITE = 1
    ACCESS_MODE_BLACK = 2

    def __init__(self, access_mode=ACCESS_MODE_NONE, access_list: list or None = None):
        self.access_mode = access_mode
        self.access_list = list(access_list) if isinstance(access_list, (list, tuple, set)) else []

    def check_access(self, fid: any) -> bool:
        if self.access_mode == AccessData.ACCESS_MODE_ALL:
            return True
        elif self.access_mode == AccessData.ACCESS_MODE_NONE:
            return False
        elif self.access_mode == AccessData.ACCESS_MODE_WHITE:
            return fid in self.access_list
        elif self.access_mode == AccessData.ACCESS_MODE_BLACK:
            return fid not in self.access_list
        else:
            return False


class AccessControl:
    # CONTROL_INSTANCE = None

    def __init__(self):
        # if AccessControl.CONTROL_INSTANCE is None:
        #     self.__take_control()
        self.__lock = threading.Lock()
        self.__token_access_table = {}

    # ------------------------------------------------------------------

    def token_valid(self, token: str):
        with self.__lock:
            return token in self.__token_access_table.keys()

    def set_token_access(self, token: str, access_data: AccessData):
        with self.__lock:
            self.__token_access_table[token] = access_data

    def get_token_access(self, token: str) -> AccessData or None:
        with self.__lock:
            return self.__token_access_table.get(token, None)

    def token_accessible(self, token: str, feature_id: str, **kwargs) -> (bool, str):
        # TODO: Check access here
        with self.__lock:
            token_access: AccessData = self.__token_access_table.get(token, None)
            if not isinstance(token_access, AccessData):
                return False, 'Access Deny'
            return (True, '') if token_access.check_access(feature_id) else (False, 'Access Deny')

    # # ---------------------------------------------------------------------------------
    #
    # @staticmethod
    # def apply(feature_name: str):
    #     def decorator(func):
    #         @functools.wraps(func)
    #         def wrapper(*args, **kwargs):
    #             token = kwargs.get('token', None)
    #             if token is None:
    #                 print('Token missing - [%s] Blocked.' % feature_name)
    #                 return 'Token missing.'
    #             if AccessControl.CONTROL_INSTANCE is None:
    #                 print('Access Control missing - [%s] Blocked' % feature_name)
    #                 return 'Access Control missing.'
    #             del kwargs['token']
    #             access, reason = AccessControl.\
    #                 CONTROL_INSTANCE.token_accessible(token, feature_name, **kwargs)
    #             return func(*args, **kwargs) if access else reason
    #         return wrapper
    #     return decorator
    #
    # # ---------------------------------------------------------------------------------
    #
    # def __take_control(self):
    #     AccessControl.CONTROL_INSTANCE = self





