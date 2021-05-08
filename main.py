import os
import sys
import traceback

from PyQt5.QtWidgets import QApplication

from StockAnalysisSystem.ui.main_ui import MainWindow
from StockAnalysisSystem.ui.Utility.ui_context import UiContext
from StockAnalysisSystem.core.Utility.ui_utility import WrapperQDialog
from StockAnalysisSystem.ui.if_selector_ui import InterfaceSelectUi
from StockAnalysisSystem.interface.interface_rest import RestInterface
from StockAnalysisSystem.interface.interface_local import LocalInterface
from StockAnalysisSystem.interface.interface import SasInterface as sasIF


def init_if(local: bool = True, local_project_path: str = '',
            remote_url: str = 'http://127.0.0.1:80/api', remote_token: str = '') -> sasIF or None:
    if local:
        if local_project_path is None or local_project_path == '':
            local_project_path = os.getcwd()
        local_if = LocalInterface()
        local_if.if_init(local_project_path)
        return local_if
    else:
        remote_if = RestInterface()
        remote_if.if_init(api_uri=remote_url, token=remote_token)
        return remote_if


def main():
    app = QApplication(sys.argv)

    if_sel_ui = InterfaceSelectUi()
    dlg = WrapperQDialog(if_sel_ui)
    dlg.exec()

    if not if_sel_ui.is_ok():
        exit(0)

    is_local = if_sel_ui.is_local()
    url, port = if_sel_ui.get_remote_host_config()
    user, passwd, token = if_sel_ui.get_remote_host_authentication()

    sasif = init_if(is_local, remote_url=url, remote_token=token)

    prob = sasif.if_prob()
    if prob is None:
        print('Interface access FAIL. Quit.')
        exit(1)

    ui_ctx = UiContext()
    ui_ctx.set_sas_interface(sasif)

    main_wnd = MainWindow(ui_ctx)
    main_wnd.show()

    sys.exit(app.exec())

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
