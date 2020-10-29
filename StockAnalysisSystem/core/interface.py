import pandas as pd
import datetime


def sas():
    from .StockAnalysisSystem import StockAnalysisSystem
    return StockAnalysisSystem()


def sas_init(project_path: str = None, config=None, not_load_config: bool = False) -> bool:
    return sas().check_initialize(project_path, config, not_load_config)


def sas_query(uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> pd.DataFrame or None:
    from .DataHubEntry import DataHubEntry
    from .DataHub.UniversalDataCenter import UniversalDataCenter
    data_hub: DataHubEntry = sas().get_data_hub_entry()
    data_center: UniversalDataCenter = data_hub.get_data_center()
    return data_center.query(uri, identity, time_serial, **extra)


def sas_update(uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> bool:
    from .DataHubEntry import DataHubEntry
    from .DataHub.UniversalDataCenter import UniversalDataCenter
    data_hub: DataHubEntry = sas().get_data_hub_entry()
    data_center: UniversalDataCenter = data_hub.get_data_center()
    return data_center.update_local_data(uri, identity, time_serial, **extra)


# def sas_analysis(securities: str or [str], analyzers: [str],
#                  time_serial: (datetime.datetime, datetime.datetime),
#                  progress_rate: ProgressRate = None,
#                  enable_calculation: bool = True,
#                  enable_from_cache: bool = True, enable_update_cache: bool = True,
#                  debug_load_json: bool = False, debug_dump_json: bool = False,
#                  dump_path: str = '') -> pd.DataFrame:
#     from .AnalyzerEntry import StrategyEntry
#     strategy_entry: StrategyEntry = sas().get_strategy_entry()
#     strategy_entry.analysis_advance()


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




