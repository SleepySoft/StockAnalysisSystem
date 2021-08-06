import functools


# import hashlib
# md5 = hashlib.md5()
# md5.update('SleepySoft'.encode('utf-8'))
# print(md5.hexdigest())

class UniversalBits:
    def __init__(self):
        self.__mask_arr = []
        self.__highest_bit = 0

    # ------------------------------------------------

    def bit_0_count(self) -> int:
        pass

    def bit_1_count(self) -> int:
        pass

    def highest_bit(self) -> int:
        return self.__highest_bit

    def reserve_bit(self, highest_bit: int, default_set=False):
        pass

    # ------------------------------------------------

    def set_bit(self, bit: int):
        pass

    def clear_bit(self, bit: int):
        pass

    def check_bit(self, bit: int) -> bool:
        pass

    # ------------------------------------------------

    def set_bits(self, bits) -> bool:
        if not isinstance(bits, UniversalBits):
            return False

    def clear_bits(self, bits) -> bool:
        if not isinstance(bits, UniversalBits):
            return False

    def check_bits(self, bits) -> bool:
        if not isinstance(bits, UniversalBits):
            return False


class AccessControl:
    CONTROL_INSTANCE = None

    def __init__(self):
        if AccessControl.CONTROL_INSTANCE is None:
            self.take_control()
        self.__access_table = {}

    def accessible(self, token: str, feature_name: str, **kwargs) -> (bool, str):
        # TODO: Check access here
        access = True
        reason = ''
        return access, reason

    def token_valid(self, token: str):
        return token in self.__access_table

    def register_feature(self, feature_name: str):
        pass

    def set_token_access(self, token: str, access_sheet: dict):
        pass

    def get_token_access(self, token: str) -> dict:
        pass

    # ---------------------------------------------------------------------------------

    def take_control(self):
        AccessControl.CONTROL_INSTANCE = self

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
                    CONTROL_INSTANCE.accessible(token, feature_name, **kwargs)
                return func(*args, **kwargs) if access else reason
            return wrapper
        return decorator






