#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5 import Qt
from PyQt5.QtWidgets import QMenu

from .config_ui import *
from .DataHubUi import *
from .strategy_ui import *
from .data_update_ui import *
from .XListTableUi import *
from .task_queue_ui import *
from ..readme import VERSION
from ..core.StockAnalysisSystem import StockAnalysisSystem


# =========================================== MainWindow ===========================================

class MainWindow(CommonMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__(hold_menu=True)

        # --------- init Member ---------

        self.__menu_config = None
        self.__menu_extension = None
        self.__translate = QtCore.QCoreApplication.translate

        # ---------- Modules and Sub Window ----------

        data_hub_entry = StockAnalysisSystem().get_data_hub_entry()
        strategy_entry = StockAnalysisSystem().get_strategy_entry()
        database_entry = StockAnalysisSystem().get_database_entry()
        update_table = database_entry.get_update_table()

        self.__data_hub_ui = DataHubUi(data_hub_entry.get_data_center())
        self.__strategy_ui = StrategyUi(data_hub_entry, strategy_entry)
        self.__data_update_ui = DataUpdateUi(data_hub_entry, update_table)

        self.__gray_list_ui = XListTableUi(database_entry.get_gray_table(), '灰名单')
        self.__black_list_ui = XListTableUi(database_entry.get_black_table(), '黑名单')
        self.__focus_list_ui = XListTableUi(database_entry.get_focus_table(), '关注名单')

        # self.__alias_table_module = database_entry.get_alias_table()
        # self.__alias_table_ui = AliasTableUi(self.__alias_table_module)
        self.__task_queue_ui = TaskQueueUi(StockAnalysisSystem().get_task_queue())

        # ---------- Deep init ----------
        self.init_ui()
        self.init_menu()
        self.init_sub_window()

        # self.modules_init()
        # self.modules_ui_init()

        self.extension_window_init()

    # ----------------------------- Setup and UI -----------------------------

    def init_ui(self):
        # widget = QWidget()
        # main_layout = QHBoxLayout()
        # widget.setLayout(main_layout)
        # self.setCentralWidget(widget)

        self.setWindowTitle('Stock Analysis System [%s] - Sleepy' % VERSION)

    def init_menu(self):
        config_action = QAction('系统配置（需要重新启动程序）', self)
        config_action.setStatusTip('系统配置')
        config_action.triggered.connect(self.on_action_config)

        self.__menu_config = QMenu('Config')
        self.__menu_config.addAction(config_action)

        self.__menu_extension = QMenu('Extension')

        menu_bar = self.menuBar()
        menu_bar.addMenu(self.menu_file)
        menu_bar.addMenu(self.menu_view)
        menu_bar.addMenu(self.__menu_config)
        menu_bar.addMenu(self.__menu_extension)
        menu_bar.addMenu(self.menu_help)

    def init_sub_window(self):
        self.add_sub_window(self.__data_update_ui, 'data_update_ui', {
            'DockName': self.__translate('main', '数据管理'),
            'DockArea': Qt.LeftDockWidgetArea,
            'DockShow': True,
            'DockFloat': False,
            'MenuPresent': True,
            'ActionTips': self.__translate('main', '数据管理'),
            'ActionShortcut': 'Ctrl+D',
        })

        self.add_sub_window(self.__strategy_ui, 'strategy_ui', {
            'DockName': self.__translate('main', '策略管理'),
            'DockArea': Qt.RightDockWidgetArea,
            'DockShow': True,
            'DockFloat': False,
            'MenuPresent': True,
            'ActionTips': self.__translate('main', '策略管理'),
            'ActionShortcut': 'Ctrl+S',
        })

        self.add_sub_window(self.__data_hub_ui, 'data_hub_ui', {
            'DockName': self.__translate('main', '数据查阅'),
            'DockArea': Qt.AllDockWidgetAreas,
            'DockShow': False,
            'DockFloat': False,
            'MenuPresent': True,
            'ActionTips': self.__translate('main', '数据查阅'),
            'ActionShortcut': 'Ctrl+B',
        })

        # -------------------------------------------------------------------------

        self.add_sub_window(self.__black_list_ui, 'black_list_ui', {
            'DockName': self.__translate('main', '黑名单'),
            'DockArea': Qt.NoDockWidgetArea,
            'DockShow': False,
            'DockFloat': True,
            'MenuPresent': True,
            'ActionTips': self.__translate('main', '黑名单'),
        })

        self.add_sub_window(self.__focus_list_ui, 'focus_list_ui', {
            'DockName': self.__translate('main', '关注名单'),
            'DockArea': Qt.NoDockWidgetArea,
            'DockShow': False,
            'DockFloat': True,
            'MenuPresent': True,
            'ActionTips': self.__translate('main', '关注名单'),
        })

        self.add_sub_window(self.__gray_list_ui, 'gray_list_ui', {
            'DockName': self.__translate('main', '灰名单'),
            'DockArea': Qt.NoDockWidgetArea,
            'DockShow': False,
            'DockFloat': True,
            'MenuPresent': True,
            'ActionTips': self.__translate('main', '灰名单'),
        })

        # -------------------------------------------------------------------------

        # self.add_sub_window(self.__alias_table_ui, 'alias_table_ui', {
        #     'DockName': self.__translate('main', '别名表（考虑废弃）'),
        #     'DockArea': Qt.NoDockWidgetArea,
        #     'DockShow': False,
        #     'DockFloat': True,
        #     'MenuPresent': True,
        #     'ActionTips': self.__translate('main', '别名表'),
        # })

        self.add_sub_window(self.__task_queue_ui, 'task_queue_ui', {
            'DockName': self.__translate('main', '任务管理'),
            'DockArea': Qt.NoDockWidgetArea,
            'DockShow': False,
            'DockFloat': True,
            'MenuPresent': True,
            'ActionTips': self.__translate('main', '任务管理'),
        })

        # -------------------------------------------------------------------------

        data_update_ui = self.get_sub_window('data_update_ui')
        strategy_ui = self.get_sub_window('strategy_ui')

        if data_update_ui is not None and strategy_ui is not None:
            self.splitDockWidget(data_update_ui.dock_wnd, strategy_ui.dock_wnd, Qt.Horizontal)

    # def modules_init(self):
    #     self.__alias_table_module.init(True)
    #
    # def modules_ui_init(self):
    #     pass
    #     self.__alias_table_ui.Init()

    def extension_window_init(self):
        sas = StockAnalysisSystem()
        extension_manager = sas.get_extension_manager()
        widgets_config = extension_manager.create_extensions_widgets(self)
        for widget, _config in widgets_config:
            self.add_sub_window(widget, _config.get('name'), {
                'DockFloat': True,
                'MenuPresent': True,
                'DockArea': Qt.AllDockWidgetAreas,
                'DockShow': _config.get('show', False),
                'DockName': _config.get('name', 'Extension'),
                'ActionTips': _config.get('name', 'Extension'),
            }, self.__menu_extension)

    # ----------------------------- UI Events -----------------------------

    def on_action_config(self):
        dlg = WrapperQDialog(ConfigUi())
        dlg.exec()

    def closeEvent(self, event):
        if StockAnalysisSystem().can_sys_quit():
            StockAnalysisSystem().finalize()
            super().closeEvent(event)
        else:
            QMessageBox.information(self,
                                    QtCore.QCoreApplication.translate('main', '无法退出'),
                                    QtCore.QCoreApplication.translate('main', '有任务正在执行中，无法退出程序'),
                                    QMessageBox.Ok, QMessageBox.Ok)
            event.ignore()




