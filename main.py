import os
import sys
import traceback

from PyQt5.QtWidgets import QApplication

from StockAnalysisSystem.ui.main_ui import MainWindow
from StockAnalysisSystem.ui.config_ui import ConfigUi
from StockAnalysisSystem.interface.interface_local import LocalInterface
from StockAnalysisSystem.interface.interface import SasInterface as sasIF


def init_if(local: bool = True) -> sasIF or None:
    if local:
        local_if = LocalInterface()
        local_if.sas_init(os.getcwd())
        return local_if
    else:
        return None


def run_ui(sasif: sasIF):
    app = QApplication(sys.argv)

    # sas = StockAnalysisSystem()
    # sas.check_initialize()

    # while not sas.is_initialized():
    #     dlg = WrapperQDialog(ConfigUi(False))
    #     dlg.exec()
    #     sas.check_initialize()

    main_wnd = MainWindow(sasif)
    main_wnd.show()
    sys.exit(app.exec())


def main():
    sasif = init_if()
    run_ui(sasif)
    print('Process Quit.')


# ----------------------------------------------------------------------------------------------------------------------

def exception_hook(_type, value, tback):
    # log the exception here
    print('Exception hook triggered.')
    print(_type)
    print(value)
    print(tback)
    # then call the default handler
    sys.__excepthook__(_type, value, tback)


if __name__ == "__main__":
    sys.excepthook = exception_hook
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass
