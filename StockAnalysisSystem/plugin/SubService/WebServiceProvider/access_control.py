import uuid
import functools
import threading
from StockAnalysisSystem.core.Utility.bidict import bidict


BUILTIN_ACCESS_GROUP = {
    'admin_group': {'default_access': True, 'access_feature': [], 'deny_feature': []}
}


BUILTIN_USER = {
    'admin': {'password': '23da39b4df4d8b2cbdd976edd4df4301', 'group': 'admin_group'},
}


# --------------------------------------------------------------------------------

class AccessData:
    ACCESS_MODE_ALL = -1
    ACCESS_MODE_NONE = 0
    ACCESS_MODE_WHITE = 1
    ACCESS_MODE_BLACK = 2

    def __init__(self):
        self.access_mode = AccessData.ACCESS_MODE_NONE
        self.access_list = []

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
    CONTROL_INSTANCE = None
    FEATURE_COUNT_LIMIT = 10240

    def __init__(self):
        if AccessControl.CONTROL_INSTANCE is None:
            self.__take_control()
        # Variants
        self.__lock = threading.Lock()
        # User & Group
        self.__access_group_table = BUILTIN_ACCESS_GROUP
        self.__user_data_table = BUILTIN_USER
        # Token
        self.__token_user_table = bidict()
        self.__token_access_table = {}

    # ------------------------------------------------------------------

    def login(self, user_name: str, password: str) -> str:
        with self.__lock:
            user_token = self.user_token(user_name)
            if len(user_token) > 0:
                del self.__token_user_table[user_token]
                del self.__token_access_table[user_token]

            auth = self.user_valid(user_name) and \
                   self.__user_data_table[user_name]['password'] == str_md5(password)
            if auth:
                new_token = uuid.uuid4()
                user_group = self.__user_data_table[user_name]['group']
                self.__token_user_table[new_token] = user_name
                self.__token_access_table[new_token] = self.__access_group_table.get(user_group, {})
            else:
                new_token = ''
            return new_token

    def user_token(self, user_name: str) -> str:
        with self.__lock:
            return self.__token_user_table.inverse.get(user_name, '')

    def user_valid(self, user_name: str):
        with self.__lock:
            return user_name in self.__user_data_table.keys()

    def token_valid(self, token: str):
        with self.__lock:
            return token in self.__token_user_table.keys()

    def token_accessible(self, token: str, feature_name: str, **kwargs) -> (bool, str):
        # TODO: Check access here
        with self.__lock:
            token_access = self.__token_access_table.get(token, None)
            if not token_access:
                return False, 'Access Deny'
            accessible = feature_name in token_access['access_feature'] if \
                            not token_access['default_access'] else \
                         feature_name not in token_access['deny_feature']
            return accessible, ('' if accessible else 'Access Deny')

    # ---------------------------------------------------------------------------------

    @staticmethod
    def apply(feature_name: str):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                token = kwargs.get('token', None)
                if token is None:
                    print('Token missing - [%s] Blocked.' % feature_name)
                    return 'Token missing.'
                if AccessControl.CONTROL_INSTANCE is None:
                    print('Access Control missing - [%s] Blocked' % feature_name)
                    return 'Access Control missing.'
                del kwargs['token']
                access, reason = AccessControl.\
                    CONTROL_INSTANCE.token_accessible(token, feature_name, **kwargs)
                return func(*args, **kwargs) if access else reason
            return wrapper
        return decorator

    # ---------------------------------------------------------------------------------

    def __take_control(self):
        AccessControl.CONTROL_INSTANCE = self





