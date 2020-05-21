from .core.StockAnalysisSystem import StockAnalysisSystem
from .core.Utiltity.plugin_manager import PluginManager


def system_entry() -> StockAnalysisSystem:
    return StockAnalysisSystem()


def get_plugin_manager(name: str) -> PluginManager:
    return system_entry().get_plugin_manager(name)






















