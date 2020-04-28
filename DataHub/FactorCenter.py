import sys
import datetime
import traceback
import pandas as pd

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Database import NoSqlRw
    from Database import UpdateTableEx
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
except Exception as e:
    sys.path.append(root_path)

    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Database import NoSqlRw
    from Database import UpdateTableEx
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
finally:
    logger = logging.getLogger('')


class FactorCenter:
    FACTOR_PROB_LENGTH = 7

    def __init__(self, data_hub, factor_plugin: PluginManager):
        self.__datehub_entry = data_hub
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
            for provide in provides:
                if provide in self.__factor_depends.keys():
                    print('Duplicate factor: ' + provide)
                self.__factor_depends[provide] = depends

    def query(self, factor_name: str or [str], time_serial: tuple, mapping: dict, extra: dict) -> pd.DataFrame or None:
        if self.__datehub_entry is None:
            return None
        if not isinstance(factor_name, (list, tuple)):
            factor_name = [factor_name]

    def calculate(self, df_in: pd.DataFrame, factor_name: str or [str], extra: dict) -> pd.DataFrame or None:
        if not isinstance(factor_name, (list, tuple)):
            factor_name = [factor_name]
        full_filled = True
        factor_depends = self.get_factor_depends(factor_name)
        for name in factor_depends:
            if name not in list(df_in.columns):
                full_filled = False
                print('Factor depends field missing: ' + name)
        if not full_filled:
            return None

        df = df_in[df_in.columns]
        for factor in factor_name:
            if factor in df.columns:
                continue
            result = self.get_plugin_manager().execute_module_function(
                self.get_plugin_manager().all_modules(), 'calculate', {
                    'df_in': df,
                    'factor': factor,
                    'extra': extra,
                }, False
            )
            if result is None or len(result) == 0:
                continue
            new_columns = result.columns - df.columns
            df[new_columns] = result

    def get_factor_depends(self, factor_name: str or [str]) -> [str]:
        if not isinstance(factor_name, (list, tuple)):
            factor_name = [factor_name]
        factor_depends = []
        for name in factor_name:
            factor_depends.extend(self.__factor_depends.get(name, []))
        return factor_depends


# ----------------------------------------------------- Test Code ------------------------------------------------------

def __build_factor_center() -> FactorCenter:
    plugin = PluginManager(path.join(root_path, 'Factor'))
    factor = FactorCenter(None, plugin)
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

























