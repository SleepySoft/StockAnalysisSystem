import sys
import datetime
import traceback
import pandas as pd

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Utiltity.common import *
    from Utiltity.dependency import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Database import NoSqlRw
    from Database import UpdateTableEx
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
except Exception as e:
    sys.path.append(root_path)

    from Utiltity.common import *
    from Utiltity.dependency import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Database import NoSqlRw
    from Database import UpdateTableEx
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
finally:
    logger = logging.getLogger('')


def wrap_list(val: any):
    return list(val) if isinstance(val, (list, tuple)) else [val]


class FactorCenter:
    FACTOR_PROB_LENGTH = 7

    def __init__(self, data_hub, database: DatabaseEntry, factor_plugin: PluginManager):
        self.__data_hub_entry = data_hub
        self.__database_entry = database
        self.__factor_plugin = factor_plugin
        self.__plugin_probs = []
        self.__factor_probs = {}
        self.__factor_depends = {}

    def get_plugin_manager(self) -> PluginManager:
        return self.__factor_plugin

    # -------------------------------------------------------------------------

    def reload_plugin(self):
        self.get_plugin_manager().refresh()
        self.__plugin_probs = self.get_plugin_manager().execute_module_function(
            self.get_plugin_manager().all_modules(), 'plugin_prob', {}, False
        )
        self.__factor_probs.clear()
        self.__factor_depends.clear()

        for plugin_prob in self.__plugin_probs:
            factor_probs = plugin_prob.get('factor')
            if isinstance(factor_probs, dict):
                for uuid, prob in factor_probs.items():
                    if prob is not None and len(prob) == FactorCenter.FACTOR_PROB_LENGTH and prob[3] is not None:
                        self.__factor_probs[uuid] = prob
                    else:
                        print('Drop factor - ' + str(uuid) + ' : ' + str(prob))

        for uuid, prob in self.__factor_probs.items():
            provides, depends, comments, _, _, _, _ = prob
            provides = wrap_list(provides)
            depends = wrap_list(depends)

            for provide in provides:
                if provide in self.__factor_depends.keys():
                    print('Duplicate factor: ' + provide)
                self.__factor_depends[provide] = depends

    def query(self, sotck_identity: str, factor_name: str or [str],
              time_serial: tuple, mapping: dict, extra: dict) -> pd.DataFrame or None:
        # if self.__data_hub_entry is None:
        #     return None
        if not isinstance(factor_name, (list, tuple)):
            factor_name = [factor_name]

        df = pd.DataFrame()
        fields_dependency, factor_dependency = self.calculate_factor_dependency(factor_name)

        for factor in factor_dependency:
            if factor in df.columns:
                continue
            result = self.get_plugin_manager().execute_module_function(
                self.get_plugin_manager().all_modules(), 'calculate', {
                    'factor': factor,
                    'identity': sotck_identity,
                    'time_serial': time_serial,
                    'mapping': mapping,
                    'data_hub': self.__data_hub_entry,
                    'database': self.__database_entry,
                    'extra': extra,
                }, True
            )
            if result is None or len(result) == 0:
                continue

            df = result[0] if len(df) == 0 else pd.merge(df, result[0], how='left', on=['stock_identity', 'period'])
        return df

    def calculate_factor_dependency(self, factor_name: str or [str]) -> (list, list):
        if not isinstance(factor_name, (list, tuple)):
            factor_name = [factor_name]
        dependency = Dependency()
        for name in factor_name:
            dependency.add_dependence(name, self.__factor_depends.get(name, []))
        dependency_list = dependency.sort_by_dependency()

        fields_dependency = []
        factor_dependency = []
        for name in dependency_list:
            if name in self.__factor_depends.keys():
                factor_dependency.append(name)
            else:
                fields_dependency.append(name)
        return fields_dependency, factor_dependency


# ----------------------------------------------------- Test Code ------------------------------------------------------

def __build_factor_center() -> FactorCenter:
    plugin = PluginManager(path.join(root_path, 'Factor'))
    factor = FactorCenter(None, None, plugin)
    return factor


def test_basic():
    factor = __build_factor_center()
    factor.reload_plugin()


def test_entry():
    test_basic()


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    test_entry()

    # If program reaches here, all test passed.
    print('All test passed.')


# ------------------------------------------------- Exception Handling -------------------------------------------------

def exception_hook(type, value, tback):
    # log the exception here
    print('Exception hook triggered.')
    print(type)
    print(value)
    print(tback)
    # then call the default handler
    sys.__excepthook__(type, value, tback)


if __name__ == "__main__":
    sys.excepthook = exception_hook
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass

























