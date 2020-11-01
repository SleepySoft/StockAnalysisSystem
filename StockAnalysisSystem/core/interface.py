import datetime
import pandas as pd

from .interface_util import *
from .AnalyzerEntry import StrategyEntry
from .StockAnalysisSystem import StockAnalysisSystem
from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.task_future import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.DataHub.UniversalDataCenter import UniversalDataCenter


@local_function
def sas() -> StockAnalysisSystem:
    return StockAnalysisSystem()


def sas_init(project_path: str = None, config=None, not_load_config: bool = False) -> bool:
    return sas().check_initialize(project_path, config, not_load_config)


def sas_query(uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> pd.DataFrame or None:
    data_hub: DataHubEntry = sas().get_data_hub_entry()
    data_center: UniversalDataCenter = data_hub.get_data_center()
    return data_center.query(uri, identity, time_serial, **extra)


def sas_update(uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> bool:
    data_hub: DataHubEntry = sas().get_data_hub_entry()
    data_center: UniversalDataCenter = data_hub.get_data_center()
    return data_center.update_local_data(uri, identity, time_serial, **extra)


def sas_start_analysis(securities: str or [str], analyzers: [str],
                       time_serial: (datetime.datetime, datetime.datetime),
                       enable_from_cache: bool = True) -> TaskFuture:
    strategy_entry: StrategyEntry = sas().get_strategy_entry()
    data_hub: DataHubEntry = sas().get_data_hub_entry()
    task = SasAnalysisTask(strategy_entry, data_hub, securities, analyzers, time_serial, enable_from_cache)
    sas().get_task_queue().append_task(task)


def sas_get_all_uri() -> [str]:
    from .DataHubEntry import DataHubEntry
    from .DataHub.UniversalDataCenter import UniversalDataCenter
    data_hub: DataHubEntry = sas().get_data_hub_entry()
    data_center: UniversalDataCenter = data_hub.get_data_center()
    data_agents = data_center.get_all_agents()
    return [agent.base_uri() for agent in data_agents]


def sas_get_all_analyzer() -> [str]:
    from .AnalyzerEntry import StrategyEntry
    strategy_entry: StrategyEntry = sas().get_strategy_entry()
    analyzer_info = strategy_entry.analyzer_info()
    return [(method_uuid, method_name, method_detail) for method_uuid, method_name, method_detail, _ in analyzer_info]




