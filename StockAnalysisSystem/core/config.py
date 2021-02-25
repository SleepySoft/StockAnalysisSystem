import json
import traceback


# How to get a tushare pro token:
#   Register an account with this link (my referral link): https://tushare.pro/register?reg=271027
#   Check your token (official document): https://tushare.pro/document/1?doc_id=39
#   How to earn your score (official document): https://tushare.pro/document/1?doc_id=13
TS_TOKEN = 'TODO: Place holder, for compatibility.'


class Config:
    CONFIG_DICT = {
        'NOSQL_DB_HOST': 'The service ip or host name of mongodb service. Default "localhost"',
        'NOSQL_DB_PORT': 'The service port of mongodb service. Default "27017"',
        'NOSQL_DB_USER': 'The user name of mongodb service. Default empty',
        'NOSQL_DB_PASS': 'The password of mongodb service. Default empty',
        'TS_TOKEN': 'The tushare token which can get from https://tushare.pro/',
        'PROXY_PROTOCOL': 'The proxy type which should be one of HTTP_PROXY and HTTPS_PROXY. Default empty',
        'PROXY_HOST': 'The proxy host and port. Default empty',
    }

    MUST_CONFIG = [('NOSQL_DB_HOST', '必须填写Mongodb服务器地址（NoSql Host），否则无法正常访问数据'),
                   ('NOSQL_DB_PORT', '必须填写Mongodb服务器端口（NoSql Port），否则无法正常访问数据'),
                   ('TS_TOKEN',      '必须填写Tushare Token，否则无法更新数据。\n'
                                     '如果没有Tushare Token，请到官方网站注册一个：https://tushare.pro/register?reg=271027\n'
                                     '如果随意填写，则数据无法正常更新。但可以使用导入的离线数据（请手动导入mongodb.zip）')]

    def __init__(self):
        self.__config_dict = {}

    def set(self, key: str, value: str):
        self.__config_dict[key] = value

    def get(self, key: str, default_value: str = '') -> str:
        return self.__config_dict.get(key, default_value)

    def get_all_config(self) -> dict:
        return self.__config_dict

    def set_all_config(self, config: dict):
        self.__config_dict = config

    def save_config(self, config_file: str = 'config.json') -> bool:
        try:
            with open(config_file, 'wt') as f:
                json.dump(self.__config_dict, f, indent=4)
            global TS_TOKEN
            TS_TOKEN = self.get('TS_TOKEN')
            return True
        except Exception as e:
            print('Save config fail.')
            print(e)
            print(traceback.format_exc())
            return False
        finally:
            pass

    def load_config(self, config_file: str = 'config.json'):
        try:
            with open(config_file, 'rt') as f:
                self.__config_dict = json.load(f)
            if self.__config_dict is None or len(self.__config_dict) == 0:
                self.__config_dict = {}
                return False
            else:
                global TS_TOKEN
                TS_TOKEN = self.get('TS_TOKEN')
            return True
        except Exception as e:
            print('Load config from %s fail.' % config_file)
            print(e)
            # print(traceback.format_exc())
            return False
        finally:
            pass

    def check_config(self) -> (bool, str):
        success, reason = True, []
        for key, tips in Config.MUST_CONFIG:
            if self.get(key) == '':
                success = False
                reason.append(tips)
        return success, '\n'.join(reason)

