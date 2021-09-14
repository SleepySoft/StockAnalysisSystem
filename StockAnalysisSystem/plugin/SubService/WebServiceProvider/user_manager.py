import time
import uuid
import hashlib
import threading
from StockAnalysisSystem.core.config import Config
from StockAnalysisSystem.core.Utility.bidict import bidict
from StockAnalysisSystem.core.Utility.encryption import md5_str
from StockAnalysisSystem.core.Utility.common import str_available


USER_DATA_PASSWORD = 'password'
USER_DATA_SESSION = 'session'
USER_DATA_TIMEOUT = 'timeout'
USER_DATA_GROUP = 'group'

USER_SESSION_LOGIN_TS = 'login_ts'


BUILTIN_USER = {
    'admin': {
        USER_DATA_PASSWORD: '23da39b4df4d8b2cbdd976edd4df4301',
        USER_DATA_GROUP: 'admin_group',
        USER_DATA_SESSION: {}
    },
}


class UserTable:
    def __init__(self):
        pass

    def user_init(self, *args, **kwargs) -> bool:
        pass

    def user_auth(self, username: str, password: str) -> bool:
        pass

    def user_exists(self, username: str):
        pass

    def user_update(self, username: str, password: str):
        pass

    @staticmethod
    def password_encrypt(password: str) -> str:
        return md5_str(password)


class UserTableJson:
    def __init__(self):
        self.__config = Config()
        super(UserTableJson, self).__init__()

    def user_init(self, user_config_file: str) -> bool:
        return self.__config.load_config(user_config_file)

    def user_auth(self, username: str, password: str) -> bool:
        user_data = self.__config.get(username)
        if not isinstance(user_data, dict):
            return False
        auth = 'password' in user_data.keys() and \
               user_data['password'] == UserTable.password_encrypt(password)
        return auth

    def user_exists(self, username: str):
        return isinstance(self.__config.get(username), dict)

    def user_update(self, username: str, user_data: dict):
        pass


class UserManager:
    def __init__(self):
        self.__lock = threading.Lock()
        self.__user_data_table = BUILTIN_USER
        self.__token_user_table = bidict()

    # ------------------------------------------------------------------------------

    def user_auth(self, username: str, password: str) -> bool:
        with self.__lock:
            auth = username in self.__user_data_table.keys() and \
                   self.__user_data_table[username]['password'] == self.encrypt_password(password)
            return auth

    def user_exists(self, username: str):
        with self.__lock:
            return self.__user_exists(username)

    def user_register(self, username: str, password: str, group: str) -> bool:
        with self.__lock:
            if not str_available(username) or not str_available(password):
                return False
            if username in self.__user_data_table.keys():
                return False
            self.__user_data_table[username] = {
                USER_DATA_PASSWORD: self.encrypt_password(password),
                USER_DATA_GROUP: group,
                USER_DATA_SESSION: {}
            }

    # ------------------------------------------------------------------------------

    def get_user_property(self, username: str, key: str) -> any:
        with self.__lock:
            if not self.__user_exists(username):
                return None
            user_data = self.__user_data_table.get(username, {})
            return user_data.get(key, None)

    def set_user_property(self, username: str, key: str, val: any):
        with self.__lock:
            if not self.__user_exists(username):
                return
            user_data = self.__user_data_table.get(username, {})
            user_data[key] = val

    # ------------------------------------------------------------------------------

    def get_user_session_data(self, username: str, key: str) -> any:
        with self.__lock:
            if not self.__user_exists(username):
                return None
            user_data = self.__user_data_table.get(username, {})
            user_session = user_data.get(USER_DATA_SESSION, {})
            return user_session.session.get(key, None)

    def set_user_session_data(self, username: str, key: str, val: any):
        with self.__lock:
            if not self.__user_exists(username):
                return
            # User data MUST exists, otherwise the update will not successful
            user_data = self.__user_data_table.get(username, {})
            if USER_DATA_SESSION in user_data.keys():
                user_data[USER_DATA_SESSION][key] = val
            else:
                user_data[USER_DATA_SESSION] = {key: val}

    # ------------------------------------------------------------------------------

    def __user_exists(self, username) -> bool:
        return username in self.__user_data_table.keys()

    @staticmethod
    def encrypt_password(password: str) -> str:
        return md5_str(password)

