import uuid
import datetime
from functools import partial

import pandas as pd

from .interface import SasInterface as sasIF
import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.DataHub.DataAgent import *
from StockAnalysisSystem.core.Utiltity.resource_task import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.AnalyzerEntry import StrategyEntry
from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem
from StockAnalysisSystem.core.Utiltity.resource_manager import ResourceManager
from StockAnalysisSystem.core.DataHub.UniversalDataCenter import UniversalDataCenter


class LocalInterface(sasIF):
    def __init__(self):
        super(LocalInterface, self).__init__()
        self.__res_mgr = ResourceManager()

    # ------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------- Interface of sasIF -----------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    def if_init(self, project_path: str = None, config=None, not_load_config: bool = False) -> bool:
        return sasApi.init(project_path, config, not_load_config)

    # ------------------------------- Resource --------------------------------

    def sas_get_resource(self, res_id: str, res_name: str or [str]) -> any or [any]:
        list_param = isinstance(res_name, (list, tuple))
        res_names = res_name if list_param else [res_name]
        res = [self.__res_mgr.get_resource(res_id, name) for name in res_names]
        return res if list_param else res[0]

    # --------------------------------- Query ---------------------------------

    def sas_query(self, uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> pd.DataFrame or None:
        return sasApi.query(uri, identity, time_serial, **extra)

    # -------------------------------- Datahub --------------------------------

    def sas_execute_update(self, uri: str, identity: str or [str] = None, force: bool = False, **extra) -> str:
        task = sasApi.post_auto_update_task(uri, identity, force, **extra)
        res_id = self.__res_mgr.add_resource('task', task)
        return res_id

    def sas_get_all_uri(self) -> [str]:
        probs = sasApi.get_data_agent_info()
        return [prob.get('uri') for prob in probs]

    def sas_get_data_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        return sasApi.get_uri_data_range(uri, identity)

    def sas_get_data_agent_probs(self) -> [dict]:
        """
        Get list of data agent prob
        :return: List of dict, dict key includes [uri, depot, identity_field, datetime_field]
        """
        probs = sasApi.get_data_agent_info()
        return [{
            'uri': uri,
            'depot': depot,
            'identity_field': identity_field,
            'datetime_field': datetime_field,
        } for uri, depot, identity_field, datetime_field in probs]

    def sas_get_data_agent_update_list(self, uri: str) -> [str]:
        agent: DataAgent = sasApi.data_center().get_data_agent(uri)
        return agent.update_list()

    # ----------------------------- Update Table -----------------------------

    def sas_get_local_data_range_from_update_table(self, update_tags: [str]) -> (datetime.datetime, datetime.datetime):
        return sasApi.get_local_data_range_from_update_table(update_tags)

    def sas_get_last_update_time_from_update_table(self, update_tags: [str]) -> datetime.datetime:
        return sasApi.get_last_update_time_from_update_table(update_tags)

    # -------------------------------- Analyzer --------------------------------

    def sas_execute_analysis(self, securities: str or [str], analyzers: [str], time_serial: (datetime, datetime),
                             enable_from_cache: bool = True, **kwargs) -> str:
        task = sasApi.post_analysis_task(securities, analyzers, time_serial, enable_from_cache, **kwargs)
        return task.get_res_id()

    def sas_get_analyzer_probs(self) -> [str]:
        """
        Get list of analyzer prob
        :return: List of dict, dict key includes [uuid, name, detail]
        """
        analyzer_info = sasApi.get_analyzer_info()
        return [{
            'uuid': method_uuid, 'name': method_name, 'detail': method_detail
        } for method_uuid, method_name, method_detail, _ in analyzer_info]

    # ------------------------------------------------------------------------------------------------------------------

    def sas_get_stock_info_list(self) -> [str]:
        return sasApi.get_stock_info_list()

    def sas_get_stock_identities(self) -> [str]:
        return sasApi.get_stock_identities()

    def sas_guess_stock_identities(self, text: str) -> [str]:
        return sasApi.guess_stock_identities(text)




