import threading

from StockAnalysisSystem.core.Utility.common import ThreadSafeSingleton
from StockAnalysisSystem.core.Utility.relative_import import RelativeImport

with RelativeImport(__file__):
    from sas_terminal import SasTerminal
    from sas_terminal import TerminalContext
    from user_manager import UserManager
    from access_control import AccessControl
    from common_render import generate_display_page


class ServiceProvider(metaclass=ThreadSafeSingleton):
    def __init__(self):
        self.__init = False
        self.__lock = threading.Lock()

        self.__sas_if = None
        self.__sas_api = None

        self.__config = None
        self.__logger = print
        self.__sas_terminal = None
        self.__user_manager = None
        self.__access_control = None

        self.__offline_analysis_result = None

    def is_inited(self) -> bool:
        return self.__init

    def check_init(self, sas_if, sas_api, config=None, logger=print) -> bool:
        final_ret = True
        with self.__lock:
            if self.__init:
                return True

            self.__sas_if = sas_if
            self.__sas_api = sas_api

            self.__config = config if config is not None else self.__sas_api.config()
            self.__logger = logger

            self.__sas_terminal = SasTerminal(self.__sas_if, self.__sas_api)
            self.__user_manager = UserManager()
            self.__access_control = AccessControl()

            ret = self.__init_offline_analysis_result()
            final_ret = ret and final_ret

            self.__init = final_ret
        return final_ret

    # def __init_sas(self) -> bool:
    #     try:
    #         self.log('Init StockAnalysisSystem...')
    #         from StockAnalysisSystem.interface.interface_local import LocalInterface
    #         # from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem
    #         self.__sas_interface = LocalInterface()
    #         self.__sas_interface.if_init(os.getcwd(), config=self.__config)
    #         # if not self.__sas_interface.sas_init(project_path=os.getcwd(), config=self.__config):
    #         #     raise Exception(sasIF.__sas().get_log_errors())
    #         self.__sas_api = sasApi
    #         self.log('Init StockAnalysisSystem Complete.')
    #         return True
    #     except Exception as e:
    #         self.__sas = None
    #         self.log(str(e))
    #         self.log(str(traceback.format_exc()))
    #         self.log('Init StockAnalysisSystem Fail')
    #         return False
    #     finally:
    #         pass

    def __init_offline_analysis_result(self) -> bool:
        self.log('Init OfflineAnalysisResult...')
        from .offline_analysis_result import OfflineAnalysisResult
        self.__offline_analysis_result = OfflineAnalysisResult(self.__logger)
        self.__offline_analysis_result.init(self.__config)
        self.log('Init OfflineAnalysisResult Complete.')
        return True

    # ---------------------------------------------------------------------------------------------------------

    def terminal_interact(self, text: str, **kwargs) -> str:
        """
        Interact with sas terminal.
        :param text: The input text
        :param kwargs: Any data that will passed to __async_terminal_interact_handler if it has async ack.
        :return: The response text
        """
        if not self.__init:
            return ''
        ctx = TerminalContext(self.__async_terminal_interact_handler, **kwargs)
        result = self.__sas_terminal.interact(ctx, text)
        return result

    def __async_terminal_interact_handler(self, **kwargs):
        pass

    # --------------------------------------------- Offline Analysis Result --------------------------------------------

    def get_security_analysis_result_url(self, security: str) -> str:
        if not self.__init:
            return ''
        if self.__offline_analysis_result is None:
            return ''
        if not self.__offline_analysis_result.security_result_exists(security):
            return ''
        return 'http://211.149.229.160/analysis?security=%s' % security

    def get_security_analysis_result_page(self, security: str) -> str:
        if not self.__init:
            return ''
        if self.__offline_analysis_result is None:
            return ''
        result_html = self.__offline_analysis_result.get_analysis_result_html(security)
        return generate_display_page('分析结果' + security, result_html)

    # ------------------------------------------------------------------------------------------------------------------

    def sys_call(self, token: str, feature: str, *args, **kwargs):
        if not self.__init:
            return ''
        access, reason = self.check_accessible(token, feature, *args, **kwargs)
        if access:
            resp = self.__sas_api.sys_call(feature, *args, **kwargs)
            return resp
        else:
            return reason

    def interface_call(self, token: str, feature: str, *args, **kwargs) -> (bool, any):
        if not self.__init:
            return ''
        access, reason = self.check_accessible(token, feature, *args, **kwargs)
        if access:
            func = getattr(self.__sas_if, feature, None)
            resp = func(*args, **kwargs) if func is not None else None
            return resp
        else:
            return reason

    def check_accessible(self, token: str, feature, *args, **kwargs):
        return self.__access_control.accessible(token, feature, **kwargs) \
            if self.__access_control is not None else False, ''

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
















