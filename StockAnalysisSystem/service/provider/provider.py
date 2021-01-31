import os
import base64
import pickle
import traceback
import pandas as pd
import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.interface.interface import SasInterface as sasIF
import StockAnalysisSystem.core.Utiltity.time_utility as sasTimeUtil
from StockAnalysisSystem.core.Utiltity.resource_manager import ResourceManager
from .user_manager import UserManager
from .access_control import AccessControl
from ..render.common_render import generate_display_page


class ServiceProvider:
    SERVICE_LIST = ['stock_analysis_system', 'offline_analysis_result']

    def __init__(self, service_table: dict):
        self.__service_table = service_table
        self.__sas_interface = None
        self.__sas_api = None

        self.__config = None
        self.__logger = print
        self.__user_manager = UserManager()
        self.__access_control = AccessControl()
        self.__resource_manager = ResourceManager()

        self.__offline_analysis_result = None

    def init(self, config) -> bool:
        final_ret = True

        from StockAnalysisSystem.core.config import Config
        self.__config = config if config is not None else Config()

        if self.__service_table.get('stock_analysis_system', False):
            ret = self.__init_sas()
            final_ret = ret and final_ret

        if self.__service_table.get('offline_analysis_result'):
            ret = self.__init_offline_analysis_result()
            final_ret = ret and final_ret

        return final_ret

    def __init_sas(self) -> bool:
        try:
            self.log('Init StockAnalysisSystem...')
            from StockAnalysisSystem.interface.interface_local import LocalInterface
            from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem
            self.__sas_interface = LocalInterface()
            self.__sas_interface.if_init(os.getcwd(), config=self.__config)
            # if not self.__sas_interface.sas_init(project_path=os.getcwd(), config=self.__config):
            #     raise Exception(sasIF.__sas().get_log_errors())
            self.__sas_api = sasApi
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

    # --------------------------------------------- Offline Analysis Result --------------------------------------------

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

    def sys_call(self, token: str, feature: str, *args, **kwargs):
        access, reason = self.check_accessible(token, feature, *args, **kwargs)
        if access:
            pass
        else:
            return reason

    def interface_call(self, token: str, feature: str, *args, **kwargs) -> (bool, any):
        access, reason = self.check_accessible(token, feature, *args, **kwargs)
        if access:
            func = getattr(self.__sas_interface, feature, None)
            resp = func(*args, **kwargs) if func is not None else None
            return resp
        else:
            return reason

    def check_accessible(self, token: str, feature, *args, **kwargs):
        return self.__access_control.accessible(token, feature, **kwargs)

    # @AccessControl.apply('query')
    # def query(self, uri: str, identity: str or None = None,
    #           since: str or None = None, until: str or None = None, **extra) -> str:
    #     if not isinstance(uri, str):
    #         return ''
    #     if isinstance(identity, str):
    #         identity = identity.split(',')
    #         identity = [s.strip() for s in identity]
    #     elif identity is None:
    #         pass
    #     else:
    #         return ''
    #     time_serial = (sasTimeUtil.text_auto_time(since),
    #                    sasTimeUtil.text_auto_time(until))
    #     if time_serial[0] is None and time_serial[1] is None:
    #         time_serial = None
    #     df = sasIF.sas_query(uri, identity, time_serial, **extra)
    #     return df

    # ------------------------------------------------------------------------------------------------------------------

    def log(self, text: str):
        if self.__logger is not None:
            self.__logger(text)

    # https://stackoverflow.com/a/57930738/12929244

    # @staticmethod
    # def serialize_dataframe(df: pd.DataFrame) -> str:
    #     pickle_bytes = pickle.dumps(df)
    #     b64_pickle_bytes = base64.b64encode(pickle_bytes)
    #     b64_pickle_bytes_str = b64_pickle_bytes.decode('utf-8')
    #     return b64_pickle_bytes_str
    #
    # @staticmethod
    # def deserialize_dataframe(b64_pickle_bytes_str: str) -> pd.DataFrame:
    #     pickle_bytes = base64.b64decode(b64_pickle_bytes_str)
    #     df = pickle.loads(pickle_bytes)
    #     return df
















