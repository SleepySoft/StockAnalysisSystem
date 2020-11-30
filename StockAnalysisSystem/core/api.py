import os
import datetime
import pandas as pd

from .api_util import *
from .Utiltity.common import *
from .DataHub.DataAgent import *
from .Utiltity.task_future import *
from .DataHubEntry import DataHubEntry
from .AnalyzerEntry import StrategyEntry
from .StockAnalysisSystem import StockAnalysisSystem
from .DataHub.UniversalDataCenter import UniversalDataCenter


# -------------------------------- System --------------------------------

def sas() -> StockAnalysisSystem:
    return StockAnalysisSystem()


def init(project_path: str = None, config=None, not_load_config: bool = False) -> bool:
    sas_path = project_path if str_available(project_path) else os.getcwd()
    return sas().check_initialize(sas_path, config, not_load_config)


# --------------------------------- Query ---------------------------------

def query(uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> pd.DataFrame or None:
    data_hub: DataHubEntry = sas().get_data_hub_entry()
    data_center: UniversalDataCenter = data_hub.get_data_center()
    return data_center.query(uri, identity, time_serial, **extra)


# -------------------------------- Datahub --------------------------------

def execute_update(uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> bool:
    data_hub: DataHubEntry = sas().get_data_hub_entry()
    data_center: UniversalDataCenter = data_hub.get_data_center()
    return data_center.update_local_data(uri, identity, time_serial, **extra)


def sas_get_data_agent_probs() -> [dict]:
    """
    Get list of data agent prob
    :return: List of dict, dict key includes [uri, depot, identity_field, datetime_field]
    """
    data_hub: DataHubEntry = sas().get_data_hub_entry()
    data_center: UniversalDataCenter = data_hub.get_data_center()
    data_agents = data_center.get_all_agents()
    return [agent.prob() for agent in data_agents]


def sas_get_data_agent_update_list(uri: str) -> [str]:
    data_hub: DataHubEntry = sas().get_data_hub_entry()
    data_center: UniversalDataCenter = data_hub.get_data_center()
    agent: DataAgent = data_center.get_data_agent(uri)
    return agent.update_list()


# -------------------------------- Analyzer --------------------------------

def execute_analysis(securities: str or [str], analyzers: [str],
                     time_serial: (datetime, datetime),
                     enable_from_cache: bool = True, **kwargs) -> TaskFuture:
    strategy_entry: StrategyEntry = sas().get_strategy_entry()
    data_hub: DataHubEntry = sas().get_data_hub_entry()
    task = SasAnalysisTask(strategy_entry, data_hub, securities, analyzers, time_serial, enable_from_cache, **kwargs)
    sas().get_task_queue().append_task(task)
    return task


def get_analyzer_info() -> [str]:
    """
    Get list of analyzer prob
    :return: [(uuid, name, detail, entry)]
    """
    strategy_entry: StrategyEntry = sas().get_strategy_entry()
    analyzer_info = strategy_entry.analyzer_info()
    return analyzer_info

# ------------------------------------------------------------------------------------------------------------------




