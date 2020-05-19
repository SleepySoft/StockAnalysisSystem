import traceback
from os import sys, path

from .Utiltity.common import *
from .DataHubEntry import DataHubEntry
from .Database.DatabaseEntry import DatabaseEntry
from .Utiltity.plugin_manager import PluginManager


class StrategyEntry:
    def __init__(self, strategy_plugin: PluginManager, data_hub: DataHubEntry, database: DatabaseEntry):
        self.__data_hub = data_hub
        self.__database = database
        self.__strategy_plugin = strategy_plugin

    def get_plugin_manager(self) -> PluginManager:
        return self.__strategy_plugin

    # ------------------------------------------------------------------------------------------------------------------

    def strategy_prob(self) -> [dict]:
        return self.get_plugin_manager().execute_module_function(
            self.get_plugin_manager().all_modules(), 'plugin_prob', {}, False)

    def run_strategy(self, securities: [str], methods: [str], **extra) -> dict:
        result = self.get_plugin_manager().execute_module_function(
            self.get_plugin_manager().all_modules(), 'analysis', {
                'securities': securities,
                'methods': methods,
                'data_hub': self.__data_hub,
                'database': self.__database,
                'extra': extra,
            }, False)

        # Flatten the nest result list
        flat_list = [item for sublist in result for item in sublist]

        # Convert list to dict
        result_table = {}
        for hash_id, results in flat_list:
            result_table[hash_id] = results
        return result_table

    def strategy_name_dict(self) -> dict:
        name_dict = {}
        probs = self.strategy_prob()
        for prob in probs:
            methods = prob.get('methods', [])
            for method in methods:
                name_dict[method[0]] = method[1]
        return name_dict


# ----------------------------------------------------------------------------------------------------------------------
#                                                         Test
# ----------------------------------------------------------------------------------------------------------------------

def __prepare_instance() -> StrategyEntry:
    root_path = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
    plugin_mgr = PluginManager(path.join(root_path, 'Analyzer'))
    plugin_mgr.refresh()
    return StrategyEntry(plugin_mgr, None, None)


def test_analyzer_prob():
    se = __prepare_instance()
    probs = se.strategy_prob()
    print(probs)


def test_score():
    se = __prepare_instance()
    result = se.run_strategy(
        ['600001.SSZ', '70000004.SESZ'],
        ['5d19927a-2ab1-11ea-aee4-eb8a702e7495', 'bc74b6fa-2ab1-11ea-8b94-03e35eea3ca4'])
    assert result['5d19927a-2ab1-11ea-aee4-eb8a702e7495'][0].score == 10
    assert result['5d19927a-2ab1-11ea-aee4-eb8a702e7495'][1].score == 40
    assert result['bc74b6fa-2ab1-11ea-8b94-03e35eea3ca4'][0].score == 90
    assert result['bc74b6fa-2ab1-11ea-8b94-03e35eea3ca4'][1].score == 60


def test_inclusive():
    se = __prepare_instance()
    result = se.run_strategy(
        ['300008.SSZ', '00000005.SESZ'],
        ['6b23435c-2ab1-11ea-99a8-3f957097f4c9', 'd0b619ba-2ab1-11ea-ac32-43e650aafd4f'])
    assert result['6b23435c-2ab1-11ea-99a8-3f957097f4c9'][0].score == 0
    assert result['6b23435c-2ab1-11ea-99a8-3f957097f4c9'][1].score == 100
    assert result['d0b619ba-2ab1-11ea-ac32-43e650aafd4f'][0].score == 100
    assert result['d0b619ba-2ab1-11ea-ac32-43e650aafd4f'][1].score == 100


def test_exclusive():
    se = __prepare_instance()
    result = se.run_strategy(
        ['500002.SSZ', '300009.SESZ'],
        ['78ffae34-2ab1-11ea-88ff-634c407b44d3', 'd905cdea-2ab1-11ea-9e79-ff65d4808d88'])
    assert result['78ffae34-2ab1-11ea-88ff-634c407b44d3'][0].score == 0
    assert result['78ffae34-2ab1-11ea-88ff-634c407b44d3'][1].score == 0
    assert result['d905cdea-2ab1-11ea-9e79-ff65d4808d88'][0].score == 0
    assert result['d905cdea-2ab1-11ea-9e79-ff65d4808d88'][1].score == 100


def test_entry():
    test_analyzer_prob()
    test_score()
    test_inclusive()
    test_exclusive()


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

