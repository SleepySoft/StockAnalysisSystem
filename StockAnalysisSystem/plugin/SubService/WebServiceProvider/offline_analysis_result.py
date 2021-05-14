import os
import json
import threading
import traceback
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from StockAnalysisSystem.core.config import Config
import StockAnalysisSystem.core.Utility.AnalyzerUtility as analyzer_util
from StockAnalysisSystem.core.Utility.relative_import import RelativeImport

with RelativeImport(__file__):
    from common_render import data_frame_to_html


class OfflineAnalysisResult:
    def __init__(self, logger: any):
        self.__logger = logger
        self.__lock = threading.Lock()
        self.__future = None
        self.__result_path = ''
        self.__name_dict_path = ''
        self.__analyzer_name_dict = {}
        self.__analysis_result_html = {}
        self.__analysis_result_table = {}

    def init(self, config: Config):
        self.__result_path = config.get('analysis_result_path', 'analysis_result.json')
        self.__name_dict_path = config.get('analysis_name_dict_path', 'analyzer_names.json')
        self.create_load_offline_data_task()

    # ------------------------------------ Load ------------------------------------

    def create_load_offline_data_task(self):
        with self.__lock:
            if self.__future is None:
                executor = ThreadPoolExecutor(1)
                self.__future = executor.submit(self.load_offline_data, self.__name_dict_path, self.__result_path)
                executor.shutdown()

    def load_offline_data(self, name_dict_path: str, result_path: str):
        analyzer_name_dict = {}
        analysis_result_table = {}

        try:
            self.log('Loading analyzer name table...')
            with open(name_dict_path, 'rt') as f:
                analyzer_name_dict = json.load(f)
            self.log('Load analyzer name table done.')
        except Exception as e:
            self.log('Load analyzer name table fail.')
            self.log(str(e))
            self.log(str(traceback.format_exc()))
        finally:
            pass
    
        try:
            with open(result_path, 'rt') as f:
                self.log('Loading analysis result...')
                analysis_result = analyzer_util.analysis_results_from_json(f)
                self.log('Convert analysis result...')
                analysis_result_table = analyzer_util.analysis_result_list_to_security_analyzer_table(analysis_result)
                analysis_result_table = {k.split('.')[0]: v for k, v in analysis_result_table.items()}
                self.log('Load analysis result done.')
        except Exception as e:
            self.log('Load analysis result fail.')
            self.log(str(e))
            self.log(str(traceback.format_exc()))
        finally:
            pass

        self.yield_loaded_offline_data(analyzer_name_dict, analysis_result_table)

    def yield_loaded_offline_data(self, analyzer_name_dict: dict, analysis_result_table: dict):
        with self.__lock:
            self.__future = None
            self.__analyzer_name_dict = analyzer_name_dict
            self.__analysis_result_table = analysis_result_table

    # -------------------------------------------------------------------------------

    def security_result_exists(self, security: str) -> bool:
        with self.__lock:
            return security in self.__analysis_result_html or security in self.__analysis_result_table

    def get_analysis_result_html(self, security: str) -> str:
        security = security.split('.')[0]

        with self.__lock:
            result = self.__analysis_result_html.get(security, None)
            if result is not None:
                return result

            if security not in self.__analysis_result_table:
                return ''

            security_analysis_result = self.__analysis_result_table[security]

        security_analysis_result_df = analyzer_util.analyzer_table_to_dataframe(security_analysis_result)
        security_analysis_result_df = security_analysis_result_df.rename(columns=self.__analyzer_name_dict)
        security_analysis_result_df = security_analysis_result_df.fillna('-')

        security_analysis_result_html = data_frame_to_html(security_analysis_result_df)
        with self.__lock:
            self.__analysis_result_html[security] = security_analysis_result_html
    
        return security_analysis_result_html

    def log(self, text: str):
        if self.__logger is not None:
            self.__logger(text)




