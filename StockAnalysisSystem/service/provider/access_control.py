import functools


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






