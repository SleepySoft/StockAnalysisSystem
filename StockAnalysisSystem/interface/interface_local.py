import uuid
import datetime
import pandas as pd

from .interface import SasInterface as sasIF
import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.DataHub.DataAgent import *
from StockAnalysisSystem.core.Utiltity.task_future import *
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

    # --------------------------------- Query ---------------------------------

    def sas_query(self, uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> pd.DataFrame or None:
        return sasApi.query(uri, identity, time_serial, **extra)

    # -------------------------------- Datahub --------------------------------

    def sas_update(self, uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> bool:
        data_hub: DataHubEntry = self.sas().get_data_hub_entry()
        data_center: UniversalDataCenter = data_hub.get_data_center()
        return data_center.update_local_data(uri, identity, time_serial, **extra)

    def sas_get_data_agent_probs(self) -> [dict]:
        """
        Get list of data agent prob
        :return: List of dict, dict key includes [uri, depot, identity_field, datetime_field]
        """
        data_hub: DataHubEntry = self.sas().get_data_hub_entry()
        data_center: UniversalDataCenter = data_hub.get_data_center()
        data_agents = data_center.get_all_agents()
        return [agent.prob() for agent in data_agents]

    def sas_get_data_agent_update_list(self, uri: str) -> [str]:
        data_hub: DataHubEntry = self.sas().get_data_hub_entry()
        data_center: UniversalDataCenter = data_hub.get_data_center()
        agent: DataAgent = data_center.get_data_agent(uri)
        return agent.update_list()

    # -------------------------------- Analyzer --------------------------------

    def sas_execute_analysis(self, securities: str or [str], analyzers: [str], time_serial: (datetime, datetime),
                             enable_from_cache: bool = True, extra: dict = {}) -> str:
        task = sasApi.execute_analysis(securities, analyzers, time_serial, enable_from_cache, **extra)
        res_id = self.__res_mgr.add_resource('task', task)
        return res_id

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




