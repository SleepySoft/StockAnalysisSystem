from os import sys

from .Utility.AnalyzerUtility import *
from .DataHubEntry import DataHubEntry
from .Database.DatabaseEntry import DatabaseEntry
from .Utility.plugin_manager import PluginManager


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
        delete_analyzer_cache = []
        analysis_result_packs = []
        for r in result_list:
            if r.period is None:
                # This kind of result comes from real-time analyzer
                # We should delete the old result then update with current time
                r.period = now().replace(microsecond=0)
                if str_available(r.method) and r.method not in delete_analyzer_cache:
                    delete_analyzer_cache.append(r.method)
            p = r.pack()
            p['period'] = text_auto_time(p['period'])
            analysis_result_packs.append(p)
        for analyzer in delete_analyzer_cache:
            self.__data_hub.get_data_center().delete_local_data(uri, analyzer=analyzer)
        self.__data_hub.get_data_center().merge_local_data(uri, '', analysis_result_packs)

    def result_from_cache(self, uri: str, analyzer: str or [str] = None, identity: str or [str] = None,
                          time_serial: tuple = None) -> pd.DataFrame:
        if analyzer is None or len(analyzer) == 0:
            df = self.__data_hub.get_data_center().query(uri, identity, time_serial)
        else:
            if isinstance(analyzer, str):
                analyzer = [analyzer]
            df = self.__data_hub.get_data_center().query(uri, identity, time_serial, analyzer=analyzer)
        return df

    def analysis_advance(self, securities: str or [str], analyzers: [str],
                         time_serial: (datetime.datetime, datetime.datetime),
                         progress_rate: ProgressRate = None,
                         enable_calculation: bool = True,
                         enable_from_cache: bool = True, enable_update_cache: bool = True,
                         debug_load_json: bool = False, debug_dump_json: bool = False,
                         dump_path: str = '') -> [AnalysisResult]:
        """
        Execute analysis and do extra job specified by param. And dump offline analysis result.
        :param securities: The securities that you want to analysis
        :param analyzers: The analyzer that you want to execute
        :param time_serial: The time range as tuple that you want to analysis
        :param progress_rate: The progress rate, None if you don't need the progress updating.
        :param enable_calculation: If False, it will only use cached data or debug json data, not do calculation.
        :param enable_from_cache: If True, it will get data from cache first. If not exists, than do calculation.
        :param enable_update_cache: If True, the calculate result (if calculation executed) will be cached.
        :param debug_load_json: If True, data will come from debug json file (not offline analysis result json).
        :param debug_dump_json: If True, data will dump to debug json file (not offline analysis result json).
        :param dump_path: The debug json and offline analysis result json dump directory (not file name).
        :return: Analysis result list
        """
        clock = Clock()
        total_result = []

        if progress_rate is not None:
            progress_rate.reset()

        if not isinstance(securities, list):
            securities = [securities]

        if progress_rate is not None:
            for analyzer in analyzers:
                progress_rate.set_progress(analyzer, 0, len(securities))
            # So the percentage of the dump progress is weight enough
            progress_rate.set_progress('dump_result_json', 0, len(securities))

        # Remove microsecond to avoid mongodb query fail.
        # time_serial = [t.replace(microsecond=0)  for t in time_serial]

        errors = []
        for analyzer in analyzers:
            result = None
            uncached = True

            if debug_load_json:
                # DEBUG: Load result from json file
                clock.reset()
                try:
                    with open(path.join(dump_path, analyzer + '.json'), 'rt') as f:
                        result = analysis_results_from_json(f)
                    if result is not None and len(result) > 0:
                        total_result.extend(result)
                    print('Analyzer %s : Load json finished, time spending: %ss' % (analyzer, clock.elapsed_s()))
                except Exception as e:
                    print('Analyzer load from json fail. Continue...')
                    print(e)
                    print(traceback.format_exc())
                finally:
                    pass
            else:
                if enable_from_cache:
                    df = self.result_from_cache('Result.Analyzer', analyzer=analyzer,
                                                identity=securities, time_serial=time_serial)
                    result = analysis_result_dataframe_to_list(df)

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
                    self.__strategy_plugin.clear_error()
                    if progress_rate is not None:
                        result = self.run_strategy(securities, [analyzer],
                                                   time_serial=time_serial, progress=progress_rate)
                    else:
                        result = self.run_strategy(securities, [analyzer], time_serial=time_serial)
                    errors.append(self.__strategy_plugin.get_last_error())
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

        errors = [err for err in errors if err[0] is not None]
        if len(errors) > 0:
            print('----------------------------- Analysis Errors -----------------------------')
            for err in errors:
                if err[0] is not None:
                    print(err[0])
                    print(err[1])
                    print('---------------------------------------------------------------------------')

        name_dict_path = os.path.join(dump_path, 'analyzer_names.json')
        full_dump_path = os.path.join(dump_path, 'analysis_result.json')

        self.dump_analysis_report(total_result, full_dump_path)
        self.dump_strategy_name_dict(name_dict_path)
        progress_rate.finish_progress('dump_result_json')

        return total_result

    # ------------------------------------------------- Export / Import ------------------------------------------------

    @staticmethod
    def dump_analysis_report(result_list: [AnalysisResult], export_path: str):
        def default_dump(obj: AnalysisResult):
            if not isinstance(obj, AnalysisResult):
                print('Warning: Not an AnalysisResult object.')
                return {}
            return obj.pack(True)
        with open(export_path, 'wt') as f:
            json.dump(result_list, f, default=default_dump)

    @staticmethod
    def load_analysis_report(import_path: str) -> [AnalysisResult]:
        def handle_object(d: dict):
            ar = AnalysisResult()
            ar.unpack(d)
            return ar
        result = []
        with open(import_path, 'rt') as f:
            result = json.load(f, object_hook=handle_object)
        return result

    def dump_strategy_name_dict(self, export_path: str):
        name_dict = self.strategy_name_dict()
        with open(export_path, 'wt') as f:
            json.dump(name_dict, f)

    # ------------------------------------------------- Error Analysis -------------------------------------------------

    def analysis_error_result(self, analysis_result: [AnalysisResult]) -> dict:
        error_dict = {}
        for result in analysis_result:
            if result.exception is not None:
                if result.method not in error_dict:
                    error_dict[result.method] = 1
                else:
                    error_dict[result.method] += 1
        return error_dict

    # ----------------------------------------------------- Report -----------------------------------------------------

    def generate_report_excel_common(self, result_list: [AnalysisResult], report_path: str,
                                     extra_data: pd.DataFrame = None):
        # ------------ Parse to Table ------------
        result_table = analysis_result_list_to_analyzer_security_table(result_list)

        # ------------- Collect Info -------------
        stock_list = self.__data_hub.get_data_utility().get_stock_list()
        stock_dict = {_id: _name for _id, _name in stock_list}
        name_dict = self.strategy_name_dict()

        # ----------- Generate report ------------
        generate_analysis_report(result_table, report_path, name_dict, stock_dict, extra_data)
