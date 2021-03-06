import os
import datetime
import pandas as pd

from .api_util import *
from .Utility.common import *
from .config import Config
from .DataHub.DataAgent import *
from .Utility.resource_task import *
from .FactorEntry import FactorCenter
from .DataHubEntry import DataHubEntry
from .AnalyzerEntry import StrategyEntry
from .DataHub.DataUtility import DataUtility
from .Database.UpdateTableEx import UpdateTableEx
from .StockAnalysisSystem import StockAnalysisSystem
from .DataHub.UniversalDataCenter import UniversalDataCenter


# -------------------------------- System --------------------------------

def sas() -> StockAnalysisSystem:
    return StockAnalysisSystem()


def config() -> Config:
    return sas().get_config()


def data_hub() -> DataHubEntry:
    return sas().get_data_hub_entry()


def data_center() -> UniversalDataCenter:
    return data_hub().get_data_center()


def data_utility() -> DataUtility:
    return data_hub().get_data_utility()


def strategy_entry() -> StrategyEntry:
    return sas().get_strategy_entry()


def database_entry() -> DatabaseEntry:
    return sas().get_database_entry()


def update_table() -> UpdateTableEx:
    return database_entry().get_update_table()


def factor_center() -> FactorCenter:
    return sas().get_factor_center()


def init(project_path: str = None, config=None, not_load_config: bool = False) -> bool:
    sas_path = project_path if str_available(project_path) else os.getcwd()
    return sas().check_initialize(sas_path, config, not_load_config)


def root_path() -> str:
    return sas().get_root_path()


def project_path() -> str:
    return sas().get_project_path()


def append_task(task: TaskQueue.Task):
    sas().get_task_queue().append_task(task)


# ----------------------------------- DataHub -----------------------------------

def query(uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> pd.DataFrame or None:
    return data_center().query(uri, identity, time_serial, **extra)


def update(uri: str, identity: str or [str] = None,
           time_serial: tuple = None, force: bool = False, **extra) -> bool:
    return data_center().update_local_data(uri, identity, time_serial, force, **extra)


# ------------------------------------ Datahub ------------------------------------

# def post_auto_update_task(uri: str, identity: str or [str] = None, force: bool = False, **extra) -> ResourceTask:
#     agent = data_center().get_data_agent(uri)
#     task = SasUpdateTask(data_hub, data_center, , force)
#     task.set_work_package(agent, identity)
#     append_task(task)
#     return task


def get_data_agents() -> [DataAgent]:
    return data_center().get_all_agents()


def get_data_agent_info() -> [dict]:
    """
    Get list of data agent prob
    :return: List of dict, dict key includes [uri, depot, identity_field, datetime_field]
    """
    data_agents = get_data_agents()
    return [agent.prob() for agent in data_agents]


def get_data_agent_update_list(uri: str) -> [str]:
    agent = data_center().get_data_agent(uri)
    return agent.update_list()


def get_uri_data_range(uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
    agent = data_center().get_data_agent(uri)
    since, until = agent.data_range(uri, identity) if agent is not None else (None, None)
    return since, until


def calc_uri_data_update_range(uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
    return data_center().calc_update_range(uri, identity)


# ----------------------------- Update Table -----------------------------

def get_local_data_range_from_update_table(update_tags: [str]) -> (datetime.datetime, datetime.datetime):
    since, until = update_table().get_since_until(update_tags)
    return since, until


def get_last_update_time_from_update_table(update_tags: [str]) -> datetime.datetime:
    latest_update = update_table().get_last_update_time(update_tags)
    return latest_update


# -------------------------------- Analyzer --------------------------------

# def post_analysis_task(securities: str or [str], analyzers: [str], time_serial: (datetime, datetime),
#                        enable_from_cache: bool = True, **kwargs) -> ResourceTask:
#     task = SasAnalysisTask(strategy_entry(), data_hub(), resource_manager(),
#                            securities, analyzers, time_serial, enable_from_cache, **kwargs)
#     append_task(task)
#     return task


def analysis(securities: str or [str], analyzers: [str],
             time_serial: (datetime.datetime, datetime.datetime),
             progress_rate: ProgressRate = None,
             enable_from_cache: bool = True,
             **kwargs):
    total_result = strategy_entry().analysis_advance(
        securities, analyzers, time_serial, progress_rate,
        enable_from_cache=enable_from_cache,
        enable_update_cache=kwargs.get('enable_update_cache', True),
        debug_load_json=kwargs.get('debug_load_json', False),
        debug_dump_json=kwargs.get('debug_dump_json', False),
        dump_path=kwargs.get('dump_path', ''),
    )
    return total_result


def get_analyzer_info() -> [str]:
    """
    Get list of analyzer prob
    :return: [(uuid, name, detail, entry)]
    """
    analyzer_info = strategy_entry().analyzer_info()
    return analyzer_info


# ---------------------------------------------------- Data Utility ----------------------------------------------------

def auto_query(identity: str or [str], time_serial: tuple, fields: [str],
               join_on: [str] = None) -> pd.DataFrame or [pd.DataFrame]:
    result = data_utility().auto_query(identity, time_serial, fields, join_on)
    return result


def get_stock_info_list():
    stock_list = data_utility().get_stock_list()
    return stock_list


def get_stock_identities():
    stock_list = data_utility().get_stock_identities()
    return stock_list


def guess_stock_identities(text: str):
    stock_list = data_utility().guess_securities(text)
    return stock_list


def get_all_industries() -> str:
    industries = data_utility().get_all_industries()
    return industries


def get_industry_stocks(industry: str) -> [str]:
    stock_list = data_utility().get_industry_stocks(industry)
    return stock_list


def stock_identity_to_name(stock_identities: str or [str]):
    return data_utility().stock_identity_to_name(stock_identities)


def get_support_index() -> dict:
    return data_utility().get_support_index()


# ------------------------------------------------------- Factor -------------------------------------------------------

def get_all_factors():
    return factor_center().get_all_factors()


def get_factor_depends(factor: str) -> [str]:
    return factor_center().get_factor_depends(factor)


def get_factor_comments(factor: str) -> str:
    return factor_center().get_factor_comments(factor)


def factor_query(stock_identity: str, factor_name: str or [str],
                 time_serial: tuple, mapping: dict, **extra) -> pd.DataFrame or None:
    return factor_center().query(stock_identity, factor_name, time_serial, mapping, extra)


# ------------------------------------------------------ Sys Call ------------------------------------------------------

def sys_call(func_name: str, *args, **kwargs):
    return sas().get_sys_call().sys_call(func_name, *args, **kwargs)


def has_sys_call(func_name: str) -> bool:
    return sas().get_sys_call().has_sys_call(func_name)


def register_sys_call(func_name: str, func_entry, replace: bool = False, **kwargs) -> bool:
    return sas().get_sys_call().register_sys_call(func_name, func_entry, replace, **kwargs)


def unregister_sys_call(func_name: str):
    return sas().get_sys_call().unregister_sys_call(func_name)


def get_sys_call_by_group(group_name: str) -> [str]:
    return sas().get_sys_call().get_sys_call_by_group(group_name)


def unregister_sys_call_by_group(group_name: str):
    return sas().get_sys_call().unregister_sys_call_by_group(group_name)

