import json
import traceback
from shutil import copyfile


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
        self.__config_root = {}

    def set(self, key: str, value: str or dict, protect: bool = True) -> bool:
        config_dict, config_name = self.__get_config_leaf(key, True)
        if not isinstance(config_dict, dict):
            print('Warning: The path is wrong, maybe the key path includes value: ' + key)
            return False
        if isinstance(config_dict.get(config_name, None), dict) and not isinstance(value, dict) and protect:
            print('Protection: If you want overwrite sub setting by simple value, please specify protect=False')
            return False
        config_dict[config_name] = value
        return True

    def get(self, key: str, default_value: str = '') -> str or dict:
        config_dict, config_name = self.__get_config_leaf(key, False)
        return config_dict.get(config_name, default_value) if isinstance(config_dict, dict) else default_value

    def update_config(self, config: dict):
        self.__config_root.update(config)

    def remove_config(self, keys: str or [str]):
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            config_dict, config_name = self.__get_config_leaf(key, False)
            if isinstance(config_dict, dict) and config_name in config_dict.keys():
                del config_dict[config_name]

    def get_all_config(self) -> dict:
        return self.__config_root

    def set_all_config(self, config: dict):
        self.__config_root = config

    def check_config(self) -> (bool, str):
        success, reason = True, []
        for key, tips in Config.MUST_CONFIG:
            if self.get(key) == '':
                success = False
                reason.append(tips)
        return success, '\n'.join(reason)

    # ------------------------------------------------------------------------

    def save_config(self, config_file: str = 'config.json', backup: bool = True) -> bool:
        if backup:
            try:
                copyfile(config_file, config_file + '.bak')
            except Exception as e:
                print('Warning: Backup config file fail: ' + str(e))
                print(traceback.format_exc())
            finally:
                pass
        try:
            with open(config_file, 'wt') as f:
                json.dump(self.__config_root, f, indent=4)
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

    def load_config(self, config_file: str = 'config.json') -> bool:
        try:
            with open(config_file, 'rt') as f:
                self.__config_root = json.load(f)
            if self.__config_root is None or len(self.__config_root) == 0:
                self.__config_root = {}
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

    # ------------------------------------------------------------------------

    def __parse_key_path(self, key: str) -> [str]:
        config_path = key.split('/')
        # Process the key starts with '/' or ends with '/'
        while len(config_path) > 0 and config_path[0] == '':
            config_path.pop(0)
        while len(config_path) > 0 and config_path[-1] == '':
            config_path.pop(-1)
        return config_path

    def __get_config_leaf(self, key: str, create) -> (dict or None, str):
        config_path = self.__parse_key_path(key)
        if len(config_path) == 0:
            return None, key
        config_name = config_path.pop(-1)
        config_dict = self.__config_root
        for _path in config_path:
            if not isinstance(config_dict, dict):
                print('Warning: The path is a value: ' + _path)
                return None, key
            if _path not in config_dict.keys():
                if create:
                    config_dict[_path] = {}
                else:
                    config_dict = None
                    break
            config_dict = config_dict[_path]
        return config_dict, config_name


# ----------------------------------------------------------------------------------------------------------------------

def test_level_1_setting():
    config = Config()
    config.set('key1', 'value1')
    config.set('key2', 'value2')
    assert config.get('key1') == 'value1'
    assert config.get('key2') == 'value2'

    config.set('key1', 'valueA')
    config.set('key2', 'valueB')
    assert config.get('key1') == 'valueA'
    assert config.get('key2') == 'valueB'
    assert config.get('/key1') == 'valueA'
    assert config.get('/key2') == 'valueB'
    assert config.get('/key1/') == 'valueA'
    assert config.get('/key2/') == 'valueB'

    config.set('/key1', 'valueX')
    config.set('/key2', 'valueY')
    assert config.get('key1') == 'valueX'
    assert config.get('key2') == 'valueY'
    assert config.get('/key1') == 'valueX'
    assert config.get('/key2') == 'valueY'
    assert config.get('/key1/') == 'valueX'
    assert config.get('/key2/') == 'valueY'

    config.set('/key1/', 'valueI')
    config.set('/key2/', 'valueII')
    assert config.get('key1') == 'valueI'
    assert config.get('key2') == 'valueII'
    assert config.get('/key1') == 'valueI'
    assert config.get('/key2') == 'valueII'
    assert config.get('/key1/') == 'valueI'
    assert config.get('/key2/') == 'valueII'


def test_level_n_setting():
    config = Config()

    config.set('key1', 'value1')
    config.set('key2', 'value2')
    config.set('key3_1/key3_2', 'value3')
    config.set('key4_1/key4_2/key4_3', 'value4')

    assert config.get('key1') == 'value1'
    assert config.get('key2') == 'value2'
    assert config.get('key3_1/key3_2') == 'value3'
    assert config.get('key4_1/key4_2/key4_3') == 'value4'
    assert isinstance(config.get('key3_1'), dict)
    assert isinstance(config.get('key4_1/key4_2'), dict)

    assert not config.set('key2/key2_2', 'value2_2')

    config.remove_config('key2')
    assert config.set('key2/key2_2', 'value2_2')
    assert isinstance(config.get('key2'), dict)
    assert config.get('key2/key2_2') == 'value2_2'

    assert not config.set('key3_1', 'any_value')
    assert config.get('key3_1/key3_2') == 'value3'

    assert config.set('key3_1', {'key3_2': {'key3_3': 'value_3_3'}})
    assert config.get('key3_1/key3_2/key3_3') == 'value_3_3'

    assert config.set('key3_1', 'value_3_1', False)
    assert config.get('key3_1') == 'value_3_1'


def test_entry():
    test_level_1_setting()
    test_level_n_setting()


def main():
    test_entry()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass
