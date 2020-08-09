import traceback
from os import sys, path

from .Utiltity.common import *
from .Utiltity.time_utility import *
from .Utiltity.AnalyzerUtility import *
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

    # ------------------------------------------------- Prob and Info --------------------------------------------------

    def strategy_prob(self) -> [dict]:
        return self.get_plugin_manager().execute_module_function(
            self.get_plugin_manager().all_modules(), 'plugin_prob', {}, False)

    def analyzer_info(self) -> [(str, str, str, str)]:
        """
        Get all analyzer info in list of tuple. Notice that do not call the entry directly.
        :return: [(uuid, name, detail, entry)]
        """
        info = []
        probs = self.strategy_prob()
        for prob in probs:
            methods = prob.get('methods', [])
            for method in methods:
                method_uuid = method[0]
                method_name = method[1]
                method_detail = method[2]
                method_entry = method[3]
                if method_entry is not None and '测试' not in method_name:
                    # Notice the item order
                    info.append((method_uuid, method_name, method_detail, method_entry))
        return info

    def strategy_name_dict(self) -> dict:
        name_dict = {}
        probs = self.strategy_prob()
        for prob in probs:
            methods = prob.get('methods', [])
            for method in methods:
                name_dict[method[0]] = method[1]
        return name_dict

    # ----------------------------------------------- Analysis and Cache -----------------------------------------------

    def run_strategy(self, securities: [str], methods: [str],
                     time_serial: tuple = (years_ago(5), now()), **kwargs) -> list:
        result = self.get_plugin_manager().execute_module_function(
            self.get_plugin_manager().all_modules(), 'analysis', {
                'methods': methods,
                'securities': securities,
                'time_serial': time_serial,
                'data_hub': self.__data_hub,
                'database': self.__database,
                **kwargs,
            }, False)

        # Flatten the nest result list
        flat_list = [item for sublist in result for item in sublist]

        return flat_list

        # # Convert list to dict
        # result_table = {}
        # for hash_id, results in flat_list:
        #     result_table[hash_id] = results
        # return result_table

    def cache_analysis_result(self, uri: str, result_list: list):
        analysis_result_packs = []
        for r in result_list:
            if r.period is None:
                # Storage with the latest quarter
                r.period = previous_quarter(now())
            analysis_result_packs.append(r.pack())
        # analysis_result_packs = [r.pack() for r in result_list if r.period is not None]
        self.__data_hub.get_data_center().merge_local_data(uri, '', analysis_result_packs)

    def result_from_cache(self, uri: str, analyzer: str or [str] = None, identity: str or [str] = None,
                          time_serial: tuple = None) -> pd.DataFrame:
        if analyzer is None or len(analyzer) == 0:
            df = self.__data_hub.get_data_center().query(uri, identity, time_serial)
        else:
            if isinstance(analyzer, str):
                analyzer = [analyzer]
            df = self.__data_hub.get_data_center().query(uri, identity, time_serial, analyzer={'$in': analyzer})
        return df

    def analysis_advance(self, securities: str or [str], analyzers: [str],
                         time_serial: (datetime.datetime, datetime.datetime),
                         progress_rate: ProgressRate = None,
                         enable_calculation: bool = True,
                         enable_from_cache: bool = True, enable_update_cache: bool = True,
                         debug_load_json: bool = False, debug_dump_json: bool = False,
                         dump_path: str = '') -> [AnalysisResult]:
        clock = Clock()
        total_result = []

        if progress_rate is not None:
            progress_rate.reset()

        if not isinstance(securities, list):
            securities = [securities]

        for analyzer in analyzers:
            progress_rate.set_progress(analyzer, 0, len(securities))

        for analyzer in analyzers:
            result = None
            uncached = True

            if debug_load_json:
                # DEBUG: Load result from json file
                clock.reset()
                with open(path.join(dump_path, analyzer + '.json'), 'rt') as f:
                    result = analysis_results_from_json(f)
                print('Analyzer %s : Load json finished, time spending: %ss' % (analyzer, clock.elapsed_s()))
            else:
                if enable_from_cache:
                    df = self.result_from_cache('Result.Analyzer', analyzer=analyzer,
                                                identity=securities, time_serial=time_serial)
                    result = analysis_dataframe_to_list(df)

                    if result is None or len(result) == 0:
                        result = None
                        print('Analyzer %s : No cache data' % analyzer)
                    else:
                        uncached = False
                        if progress_rate is not None:
                            progress_rate.finish_progress(analyzer)
                        print('Analyzer %s : Load cache finished, time spending: %ss' % (analyzer, clock.elapsed_s()))

                if result is None and enable_calculation:
                    clock.reset()
                    if progress_rate is not None:
                        result = self.run_strategy(securities, [analyzer],
                                                   time_serial=time_serial, progress=progress_rate)
                    else:
                        result = self.run_strategy(securities, [analyzer], time_serial=time_serial)
                    print('Analyzer %s : Execute analysis, time spending: %ss' % (analyzer, clock.elapsed_s()))

                if result is not None and len(result) > 0:
                    total_result.extend(result)
                    byte_size = sys.getsizeof(total_result) + sum(r.rough_size() for r in total_result)
                    print('Total result size = %.2f MB' % (float(byte_size) / 1024 / 1024))

                    if debug_dump_json:
                        # DEBUG: Dump result to json file
                        clock.reset()
                        with open(path.join(dump_path, analyzer + '.json'), 'wt') as f:
                            analysis_results_to_json(result, f)
                        print('Analyzer %s : Dump json, time spending: %ss' % (analyzer, clock.elapsed_s()))

                    if uncached and enable_update_cache:
                        clock.reset()
                        self.cache_analysis_result('Result.Analyzer', result)
                        print('Analyzer %s : Cache result, time spending: %ss' % (analyzer, clock.elapsed_s()))
        return total_result

    # ----------------------------------------------------- Report -----------------------------------------------------

    def generate_report_excel_common(self, result_list: [AnalysisResult], report_path: str,
                                     extra_data: pd.DataFrame = None):
        # ------------ Parse to Table ------------
        result_table = analysis_result_list_to_table(result_list)

        # ------------- Collect Info -------------
        stock_list = self.__data_hub.get_data_utility().get_stock_list()
        stock_dict = {_id: _name for _id, _name in stock_list}
        name_dict = self.strategy_name_dict()

        # ----------- Generate report ------------
        generate_analysis_report(result_table, report_path, name_dict, stock_dict, extra_data)


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

