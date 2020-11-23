import datetime
import pandas as pd

from .interface_util import *
from .interface import interface as sas_interface
from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.task_future import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.AnalyzerEntry import StrategyEntry
from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem
from StockAnalysisSystem.core.DataHub.UniversalDataCenter import UniversalDataCenter


class LocalInterface(sas_interface):
    def __init__(self):
        super(LocalInterface, self).__init__()

    def sas_init(self, project_path: str = None, config=None, not_load_config: bool = False) -> bool:
        return self.__sas().check_initialize(project_path, config, not_load_config)

    def sas_query(self, uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> pd.DataFrame or None:
        data_hub: DataHubEntry = self.__sas().get_data_hub_entry()
        data_center: UniversalDataCenter = data_hub.get_data_center()
        return data_center.query(uri, identity, time_serial, **extra)

    def sas_update(self, uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> bool:
        data_hub: DataHubEntry = self.__sas().get_data_hub_entry()
        data_center: UniversalDataCenter = data_hub.get_data_center()
        return data_center.update_local_data(uri, identity, time_serial, **extra)

    def sas_start_analysis(self, securities: str or [str], analyzers: [str],
                           time_serial: (datetime, datetime),
                           enable_from_cache: bool = True) -> TaskFuture:
        strategy_entry: StrategyEntry = self.__sas().get_strategy_entry()
        data_hub: DataHubEntry = self.__sas().get_data_hub_entry()
        task = SasAnalysisTask(strategy_entry, data_hub, securities, analyzers, time_serial, enable_from_cache)
        self.__sas().get_task_queue().append_task(task)

    def sas_get_all_uri(self) -> [str]:
        data_hub: DataHubEntry = self.__sas().get_data_hub_entry()
        data_center: UniversalDataCenter = data_hub.get_data_center()
        data_agents = data_center.get_all_agents()
        return [agent.base_uri() for agent in data_agents]

    def sas_get_all_analyzer(self) -> [str]:
        strategy_entry: StrategyEntry = self.__sas().get_strategy_entry()
        analyzer_info = strategy_entry.analyzer_info()
        return [(method_uuid, method_name, method_detail) for method_uuid, method_name, method_detail, _ in analyzer_info]

    # ------------------------------------------------------------------------------------------------------------------

    def __sas(self) -> StockAnalysisSystem:
        return StockAnalysisSystem()




