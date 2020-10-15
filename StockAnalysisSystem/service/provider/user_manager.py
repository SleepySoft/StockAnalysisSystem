import time
import hashlib


class UserData:
    def __init__(self):
        self.name = ''
        self.login_time = 0
        self.user_session = {}


class UserManager:
    def __init__(self):
        self.__user_data = {}

    def login(self, username: str, passowrd: str) -> bool:
        passwd_sha1 = hashlib.sha1(passowrd.encode('utf-8')).hexdigest()
        if username == 'Sleepy' and passwd_sha1 == '4181a3ababceb12d8cf21523e7eafefb46f7326f':
            user_data = self.get_user_data(username, True)
            user_data.login_time = time.time()
            return True
        else:
            return False

    def logoff(self, username: str, remove_session: bool = False) -> bool:
        user_data = self.get_user_data(username, False)
        if user_data is not None:
            if user_data.login_time > 0:
                ret = True
                user_data.login_time = 0
            else:
                ret = False
            if remove_session:
                del self.__user_data[username]
            return ret
        else:
            return False

    def is_user_login(self, username: str):
        user_data = self.__user_data.get(username, None)
        return user_data is not None and user_data.login_time > 0

    def get_user_data(self, username: str, create: bool = False) -> UserData or None:
        user_data = self.__user_data.get(username, None)
        if user_data is None and create:
            user_data = UserData()
            user_data.name = username
            self.__user_data[username] = user_data
        return user_data

    def update_user_session(self, username: str, key: str, val: any):
        user_data = self.get_user_data(username, True)
        if user_data is not None:
            user_data.session[key] = val

    def get_user_session(self, username: str, key: str):
        user_data = self.get_user_data(username, False)
        return None if user_data is None else user_data.session.get(key)


