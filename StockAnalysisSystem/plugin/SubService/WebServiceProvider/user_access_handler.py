import threading

from .user_manager import *
from .access_control import *


class UserAccessHandler:
    DEFAULT_LOGIN_TIMEOUT = 1 * 60 * 60         # second

    def __init__(self, user_manager: UserManager, access_control: AccessControl):
        self.__user_manager = user_manager
        self.__access_control = access_control

        self.__lock = threading.Lock()
        self.__token_user_table = bidict()

        self.__group_access_table = {}

    def init(self):
        self.__init_group_config()
        self.__load_group_config()

    # ---------------------------------------------------------------------------

    def login(self, username: str, password: str) -> str:
        with self.__lock:
            if self.__user_manager.user_auth(username, password):
                # If multiple login allowed. Just return existing token and renew.
                self.__logoff(username)

                new_token = str(uuid.uuid4())
                self.__token_user_table[new_token] = username

                user_group = self.__user_manager.get_user_property(username, USER_FIELD_GROUP)
                group_access = self.__group_access_table.get(user_group, AccessData(AccessData.ACCESS_MODE_NONE))
                self.__access_control.set_token_access(new_token, group_access)

                self.__renew_user(username)
            else:
                new_token = ''
            return new_token

    def logoff(self, username: str, remove_session: bool = False):
        with self.__lock:
            self.__logoff(username)

        # user_data = self.get_user_data(username, False)
        # if user_data is not None:
        #     if user_data.login_time > 0:
        #         ret = True
        #         user_data.login_time = 0
        #     else:
        #         ret = False
        #     if remove_session:
        #         del self.__user_data[username]
        #     return ret
        # else:
        #     return False

    def is_user_login(self, username: str):
        user_data = self.__user_data.get(username, None)
        return user_data is not None and user_data.login_time > 0

    # ------------------------------------------------------------------------------

    def __logoff(self, username: str or None = None, user_token: str or None = None):
        if str_available(username):
            user_token = self.__token_user_table.inverse.get(username, '')
        if str_available(user_token) and user_token in self.__token_user_table.keys():
            del self.__token_user_table[user_token]

    def __renew_user(self, username: str):
        timeout = self.__user_manager.get_user_property(username, USER_FIELD_TIMEOUT)
        timeout = self.DEFAULT_LOGIN_TIMEOUT if timeout is None else timeout
        self.__user_manager.set_user_session_data(username, USER_FIELD_TIMEOUT, timeout)

    def __init_group_config(self):
        self.__group_access_table = {
            'admin_group': AccessData(AccessData.ACCESS_MODE_ALL),
            'guest_group': AccessData(AccessData.ACCESS_MODE_NONE),
            'visit_group': AccessData(AccessData.ACCESS_MODE_WHITE, []),
        }

    def __load_group_config(self):
        pass


