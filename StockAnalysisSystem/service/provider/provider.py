import base64
import pickle
import traceback
import pandas as pd
from .user_manager import UserManager
from .access_control import AccessControl
from ..render.common_render import generate_display_page


class ServiceProvider:
    SERVICE_LIST = ['stock_analysis_system', 'offline_analysis_result']

    def __init__(self, service_table: dict):
        self.__service_table = service_table

        self.__config = None
        self.__logger = print
        self.__user_manager = UserManager()
        self.__access_control = AccessControl()

        self.__sas = None
        self.__offline_analysis_result = None

    def init(self) -> bool:
        final_ret = True

        from StockAnalysisSystem.core.config import Config
        self.__config = Config()

        if self.__service_table.get('stock_analysis_system'):
            ret = self.__init_sas()
            final_ret = ret and final_ret

        if self.__service_table.get('offline_analysis_result'):
            ret = self.__init_offline_analysis_result()
            final_ret = ret and final_ret

        return final_ret

    def __init_sas(self) -> bool:
        try:
            self.log('Init StockAnalysisSystem...')
            from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem
            self.__sas = StockAnalysisSystem()
            if not self.__sas.check_initialize():
                raise Exception(self.__sas.get_log_errors())
            self.log('Init StockAnalysisSystem Complete.')
            return True
        except Exception as e:
            self.__sas = None
            self.log(str(e))
            self.log(str(traceback.format_exc()))
            self.log('Init StockAnalysisSystem Fail')
            return False
        finally:
            pass

    def __init_offline_analysis_result(self) -> bool:
        self.log('Init OfflineAnalysisResult...')
        from .offline_analysis_result import OfflineAnalysisResult
        self.__offline_analysis_result = OfflineAnalysisResult(self.__logger)
        self.__offline_analysis_result.init(self.__config)
        self.log('Init OfflineAnalysisResult Complete.')
        return True

    # ------------------------------------------------------------------------------------------------------------------

    def get_security_analysis_result_url(self, security: str) -> str:
        if self.__offline_analysis_result is None:
            return ''
        if not self.__offline_analysis_result.security_result_exists(security):
            return ''
        return 'http://211.149.229.160/analysis?security=%s' % security

    def get_security_analysis_result_page(self, security: str) -> str:
        if self.__offline_analysis_result is None:
            return ''
        result_html = self.__offline_analysis_result.get_analysis_result_html(security)
        return generate_display_page('分析结果' + security, result_html)

    # ------------------------------------------------------------------------------------------------------------------

    # https://stackoverflow.com/a/57930738/12929244

    @staticmethod
    def serialize_dataframe(df: pd.DataFrame) -> str:
        pickbytes = pickle.dumps(df)
        b64_pickbytes = base64.b64encode(pickbytes)
        return b64_pickbytes

    @staticmethod
    def deserialize_dataframe(b64_pickbytes: str) -> pd.DataFrame:
        pickbytes = base64.b64decode(b64_pickbytes)
        df = pickle.loads(pickbytes)
        return df

    def log(self, text: str):
        if self.__logger is not None:
            self.__logger(text)
















