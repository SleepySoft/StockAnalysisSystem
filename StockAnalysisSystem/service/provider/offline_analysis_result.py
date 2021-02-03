import json
import traceback
import pandas as pd

from ..render.common_render import data_frame_to_html
from StockAnalysisSystem.core.config import Config
import StockAnalysisSystem.core.Utility.AnalyzerUtility as analyzer_util


class OfflineAnalysisResult:
    def __init__(self, logger: any):
        self.__logger = logger
        self.__analyzer_name_dict = {}
        self.__analysis_result_html = {}
        self.__analysis_result_table = {}

    def init(self, config: Config):
        result_path = config.get('analysis_result_path', 'analysis_result.json')
        name_dict_path = config.get('analysis_name_dict_path', 'analyzer_names.json')
    
        try:
            self.log('Loading analyzer name table...')
            with open(name_dict_path, 'rt') as f:
                self.__analyzer_name_dict = json.load(f)
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
                self.__analysis_result_table = analyzer_util.analysis_result_list_to_security_analyzer_table(analysis_result)
                self.__analysis_result_table = {k.split('.')[0]: v for k, v in self.__analysis_result_table.items()}
                self.log('Load analysis result done.')
        except Exception as e:
            self.log('Load analysis result fail.')
            self.log(str(e))
            self.log(str(traceback.format_exc()))
        finally:
            pass

    def security_result_exists(self, security: str) -> bool:
        return security in self.__analysis_result_html or security in self.__analysis_result_table

    def get_analysis_result_html(self, security: str) -> str:
        security = security.split('.')[0]
    
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
        self.__analysis_result_html[security] = security_analysis_result_html
    
        return security_analysis_result_html

    def log(self, text: str):
        if self.__logger is not None:
            self.__logger(text)




