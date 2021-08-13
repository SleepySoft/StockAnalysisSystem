import time
import uuid
import hashlib
import threading
from StockAnalysisSystem.core.Utility.bidict import bidict
from StockAnalysisSystem.core.Utility.encryption import md5_str
from StockAnalysisSystem.core.Utility.common import str_available


USER_FIELD_PASSWORD = 'password'
USER_FIELD_SESSION = 'session'
USER_FIELD_TIMEOUT = 'timeout'
USER_FIELD_GROUP = 'group'


BUILTIN_USER = {
    'admin': {
        USER_FIELD_PASSWORD: '23da39b4df4d8b2cbdd976edd4df4301',
        USER_FIELD_GROUP: 'admin_group',
        USER_FIELD_SESSION: {}
    },
}


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
                USER_FIELD_PASSWORD: self.encrypt_password(password),
                USER_FIELD_GROUP: group,
                USER_FIELD_SESSION: {}
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
            user_session = user_data.get(USER_FIELD_SESSION, {})
            return user_session.session.get(key, None)

    def set_user_session_data(self, username: str, key: str, val: any):
        with self.__lock:
            if not self.__user_exists(username):
                return
            # User data MUST exists, otherwise the update will not successful
            user_data = self.__user_data_table.get(username, {})
            if USER_FIELD_SESSION in user_data.keys():
                user_data[USER_FIELD_SESSION][key] = val
            else:
                user_data[USER_FIELD_SESSION] = {key: val}

    # ------------------------------------------------------------------------------

    def __user_exists(self, username) -> bool:
        return username in self.__user_data_table.keys()

    @staticmethod
    def encrypt_password(password: str) -> str:
        return md5_str(password)

