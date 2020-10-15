import pandas as pd
from .StockAnalysisSystem import StockAnalysisSystem


def sas() ->StockAnalysisSystem:
    return StockAnalysisSystem()


def sas_init(project_path: str = None, not_load_config: bool = False) -> bool:
    return sas().check_initialize(project_path, not_load_config)


def sas_query(uri: str, identity: str or [str] = None,
              time_serial: tuple = None, **extra) -> pd.DataFrame or None:
    from .DataHubEntry import DataHubEntry
    from .DataHub.UniversalDataCenter import UniversalDataCenter
    data_hub: DataHubEntry = sas().get_data_hub_entry()
    data_center: UniversalDataCenter = data_hub.get_data_center()
    return data_center.query(uri, identity, time_serial, **extra)


def sas_analysis() -> pd.DataFrame:
    from .AnalyzerEntry import StrategyEntry
    strategy_entry: StrategyEntry = sas().get_strategy_entry()
    strategy_entry.analysis_advance()


def sas_get_all_uri() -> [str]:
    pass

def sas_get_all_analyzer() -> [str]:
    pass




