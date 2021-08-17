import datetime
import threading
import time

from .user_manager import *
from .access_control import *


class AccessHandler:
    """
    Stock analysis system access handler. Use Token to identify access control.
        You can specify a static Token (never expired).
        Or login as a user to get a random Token (will expired after specified time).
    """

    DEFAULT_LOGIN_TIMEOUT = 1 * 60 * 60         # second
    ACCESS_HANDLE_INSTANCE = None
    DEFAULT_TOKEN = ''

    def __init__(self, user_manager: UserManager, access_control: AccessControl):
        self.__user_manager = user_manager
        self.__access_control = access_control

        self.__lock = threading.Lock()

        self.__token_user_table = bidict()
        self.__token_expire_table = {}
        self.__group_access_table = {}

        if AccessHandler.ACCESS_HANDLE_INSTANCE is None:
            AccessHandler.ACCESS_HANDLE_INSTANCE = self

    def init(self):
        self.__init_group_config()
        self.__load_group_config()
        self.__init_static_token()

    # ---------------------------------------------------------------------------

    def login(self, username: str, password: str) -> str:
        with self.__lock:
            if self.__user_manager.user_auth(username, password):
                # If multiple login allowed. Just return existing token and renew.
                self.__logoff(username)

                new_token = str(uuid.uuid4())
                self.__token_user_table[new_token] = username

                user_group = self.__user_manager.get_user_property(username, USER_DATA_GROUP)
                group_access = self.__group_access_table.get(user_group, AccessData(AccessData.ACCESS_MODE_NONE))
                self.__access_control.set_token_access(new_token, group_access)

                self.__user_manager.set_user_session_data(username, USER_SESSION_LOGIN_TS, int(time.time()))
                self.__renew_token(new_token)
            else:
                new_token = ''
            return new_token

    def logoff(self, username: str, remove_session: bool = False):
        with self.__lock:
            self.__logoff(username)

    def is_user_login(self, username: str) -> bool:
        with self.__lock:
            token = self.__check_user_login(username)
            return str_available(token)

    # --------------------------------------------------

    def get_user_token(self, username: str) -> str:
        with self.__lock:
            token = self.__check_user_login(username)
            return token

    def user_accessible(self, username: str, feature_id: any, **kwargs) -> (bool, str):
        with self.__lock:
            token = self.__check_user_login(username)
            if not str_available(token):
                return False, ''
            return self.__access_control.token_accessible(token, feature_id, **kwargs)

    # --------------------------------------------------

    def get_token_user(self, token: str) -> str:
        with self.__lock:
            return self.__token_user_table.get(token, '')

    def token_accessible(self, token: str, feature_id: any, **kwargs) -> (bool, str):
        with self.__lock:
            if token not in self.__token_user_table.keys():
                return False, ''
            username = self.__token_user_table.get(token, '')
            if not str_available(username):
                return False, ''
            if self.__token_expired(username):
                self.__logoff(user_token=token)
                return False, ''
            return self.__access_control.token_accessible(token, feature_id, **kwargs)

    # ------------------------------------------------------------------------------

    def __init_group_config(self):
        self.__group_access_table = {
            'admin_group': AccessData(AccessData.ACCESS_MODE_ALL),
            'guest_group': AccessData(AccessData.ACCESS_MODE_NONE),
            'visit_group': AccessData(AccessData.ACCESS_MODE_WHITE, []),
        }

    def __load_group_config(self):
        pass

    def __init_static_token(self):
        self.__access_control.set_token_access('', AccessData(AccessData.ACCESS_MODE_ALL))

    # ------------------------------------------------------------------------------

    def __logoff(self, username: str or None = None, user_token: str or None = None):
        if str_available(username):
            user_token = self.__token_user_table.inverse.get(username, '')
        if str_available(user_token) and user_token in self.__token_user_table.keys():
            del self.__token_user_table[user_token]

    def __renew_token(self, token: str):
        username = self.__token_user_table.get(token, '')
        if str_available(username):
            timeout = self.__user_manager.get_user_property(username, USER_DATA_TIMEOUT)
            timeout = self.DEFAULT_LOGIN_TIMEOUT if timeout is None else timeout
            self.__token_expire_table[token] = int(time.time()) + timeout

    def __token_expired(self, username: str) -> bool:
        """
        Check login timeout.
        :param username: User Name
        :return: True if login timeout else False
        """
        timeout_ts = self.__user_manager.get_user_session_data(username, USER_SESSION_LOGIN_TIMEOUT)
        return (timeout_ts <= int(time.time())) if timeout_ts is not None else True

    def __check_user_login(self, username: str, renew: bool = False) -> str:
        """
        Check user login availability. If login expired, it will auto logoff for the user.
        :param username: User name
        :param renew: Ture to renew user login timeout if user login available.
        :return: User token str if login valid else empty str
        """
        token = self.__user_token(username)
        if not str_available(token):
            return ''
        if self.__token_expired(username):
            self.__logoff(username=username)
            return ''
        if renew:
            self.__renew_token(username)
        return token

    # ------------------------------------------------------------------------------

    @staticmethod
    def apply(feature_name: str):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                token = kwargs.get('token', None)
                if token is None:
                    print('Token missing - [%s] Blocked.' % feature_name)
                    return 'Token missing.'
                del kwargs['token']

                if AccessHandler.ACCESS_HANDLE_INSTANCE is None:
                    print('Access Control missing - [%s] Blocked' % feature_name)
                    return 'Access Control missing.'

                access, reason = AccessHandler.\
                    ACCESS_HANDLE_INSTANCE.token_accessible(token, feature_name, **kwargs)
                return func(*args, **kwargs) if access else reason
            return wrapper
        return decorator
