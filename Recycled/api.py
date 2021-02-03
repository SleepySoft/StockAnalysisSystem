import os

from StockAnalysisSystem.ui.main_ui import MainWindow
from StockAnalysisSystem.ui.config_ui import ConfigUi

from StockAnalysisSystem.core.config import Config
from StockAnalysisSystem.core.Utility.common import *
from StockAnalysisSystem.core.Utility.ui_utility import *
from StockAnalysisSystem.core.Utility.plugin_manager import PluginManager

from StockAnalysisSystem.core.FactorEntry import FactorCenter
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.AnalyzerEntry import StrategyEntry
# from StockAnalysisSystem.core.ExtensionEntry import ExtensionManager

from StockAnalysisSystem.core.DataHub.DataAgent import DataAgent
from StockAnalysisSystem.core.DataHub.DataUtility import DataUtility
from StockAnalysisSystem.core.DataHub.UniversalDataCenter import UniversalDataCenter

from StockAnalysisSystem.core.Database.DatabaseEntry import DatabaseEntry

from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem


# ---------------------------------- Execution Entry ----------------------------------

def main(project_path: str = None):
    sas_path = project_path if str_available(project_path) else os.getcwd()
    init(sas_path)
    run_ui()


def init(project_path: str = None, not_load_config: bool = False) -> bool:
    return sas().check_initialize(project_path, not_load_config)


def error_log() -> [str]:
    return sas().get_log_errors()


def config_list() -> dict:
    return Config.CONFIG_DICT


def config_set(key: str, value: any):
    sas().get_config().set(key, value)


def config_get(key: str or None) -> dict or any:
    return sas().get_config().get_all_config() if key is None else sas().get_config().get(key, '')


def run_ui():
    app = QApplication(sys.argv)

    sas = StockAnalysisSystem()
    sas.check_initialize()

    while not sas.is_initialized():
        dlg = WrapperQDialog(ConfigUi(False))
        dlg.exec()
        sas.check_initialize()

    main_wnd = MainWindow()
    main_wnd.show()
    sys.exit(app.exec())


# -------------------------------- Module Access Entry --------------------------------

# ----------------- System Entry -----------------

def sas() -> StockAnalysisSystem:
    return StockAnalysisSystem()


# ----------- Top Level Component Entry -----------

def get_plugin_manager(name: str) -> PluginManager:
    return sas().get_plugin_manager(name)


def get_database_entry() -> DatabaseEntry:
    return sas().get_database_entry()


def get_data_hub_entry() -> DataHubEntry:
    return sas().get_data_hub_entry()


def get_strategy_entry() -> StrategyEntry:
    return sas().get_strategy_entry()


# def get_extension_manager() -> ExtensionManager:
#     return sas().get_extension_manager()


def get_factor_center() -> FactorCenter:
    return sas().get_factor_center()


# ---------- Second Level Component Entry ----------

def get_data_center() -> UniversalDataCenter:
    return get_data_hub_entry().get_data_center()


def get_data_utility() -> DataUtility:
    return get_data_hub_entry().get_data_utility()


# ----------------------------------- Data Access -----------------------------------

def query_data(uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> pd.DataFrame or None:
    return get_data_center().query(uri, identity, time_serial, **extra)


def update_data(uri: str, identity: str or [str] = None, time_serial: tuple = None, force: bool = False, **extra):
    return get_data_center().update_local_data(uri, identity, time_serial, force, **extra)


def query_online(uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> pd.DataFrame or None:
    return get_data_center().query_from_plugin(uri, identity, time_serial, **extra)


# ----------------------------------- Development -----------------------------------

def add_plugin_path(name: str, plugin_path: str):
    plugin = get_plugin_manager(name)
    if plugin is not None:
        plugin.add_plugin_path(plugin_path)
        if name == 'Extension':
            print('Extension plugin cannot be dynamically update.')
        plugin.refresh()


def register_data_agent(agent: DataAgent):
    return get_data_center().register_data_agent(agent)


def get_data_agent(uri: str or None = None) -> DataAgent:
    return get_data_center().get_data_agent(uri) if str_available(uri) else get_data_center().get_all_agents()










