from StockAnalysisSystem.ui.main_ui import MainWindow
from StockAnalysisSystem.ui.config_ui import ConfigUi
from .core.Utiltity.plugin_manager import PluginManager
from StockAnalysisSystem.core.Utiltity.ui_utility import *
from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem


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


def sas() -> StockAnalysisSystem:
    return StockAnalysisSystem()


def get_plugin_manager(name: str) -> PluginManager:
    return sas().get_plugin_manager(name)






















