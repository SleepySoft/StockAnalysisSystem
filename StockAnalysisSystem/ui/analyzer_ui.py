#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2017/08/08
@file: DataTable.py
@function:
@modify:
"""
import os

from PyQt5.QtWidgets import QLineEdit, QFileDialog, QCheckBox, QDateTimeEdit, QGridLayout

from StockAnalysisSystem.core.Utility.common import ProgressRate
from StockAnalysisSystem.core.Utility.ui_utility import *
from StockAnalysisSystem.core.Utility.TableViewEx import *
from StockAnalysisSystem.core.Utility.time_utility import *

from StockAnalysisSystem.ui.Utility.ui_context import UiContext
from StockAnalysisSystem.core.Utility.resource_sync import ResourceTagUpdater, ResourceUpdateTask


# # ------------------------- Analysis Task -------------------------
#
# class AnalysisTask(TaskQueue.Task):
#     OPTION_CALC = 1
#     OPTION_FROM_CACHE = 2
#     OPTION_UPDATE_CACHE = 16
#     OPTION_AUTO = OPTION_CALC | OPTION_FROM_CACHE | OPTION_UPDATE_CACHE
#
#     OPTION_LOAD_JSON = 1024
#     OPTION_DUMP_JSON = 2048
#     OPTION_LOAD_DUMP_ALL = 4096
#
#     OPTION_ATTACH_BASIC_INDEX = 4096
#
#     def __init__(self, ui, strategy_entry: StrategyEntry, data_hub: DataHubEntry,
#                  selector_list: [str], analyzer_list: [str], time_serial: tuple,
#                  options: int, report_path: str, progress_rate: ProgressRate):
#         super(AnalysisTask, self).__init__('AnalysisTask')
#         self.__ui = ui
#         self.__options = options
#         self.__data_hub = data_hub
#         self.__strategy = strategy_entry
#         self.__selector_list = selector_list
#         self.__analyzer_list = analyzer_list
#         self.__time_serial = time_serial
#         self.__report_path = report_path
#         self.__progress_rate = progress_rate
#
#     def run(self):
#         print('Analysis task start.')
#
#         clock = Clock()
#         stock_list = self.select()
#         result_list = self.analysis(stock_list)
#         stock_metrics = self.fetch_stock_metrics()
#         self.gen_report(result_list, stock_metrics)
#
#         print('Analysis task finished, time spending: ' + str(clock.elapsed_s()) + ' s')
#
#         self.__ui.notify_task_done()
#
#     def identity(self) -> str:
#         return 'AnalysisTask'
#
#     # -----------------------------------------------------------------------------
#
#     def select(self) -> [str]:
#         data_utility = self.__data_hub.get_data_utility()
#         stock_list = data_utility.get_stock_identities()
#         return stock_list
#
#     def analysis(self, securities_list: [str]) -> [AnalysisResult]:
#         clock_all = Clock()
#         full_dump_path = os.path.join(StockAnalysisSystem().get_project_path(), 'TestData', 'analysis_result.json')
#         if self.__options & AnalysisTask.OPTION_LOAD_JSON != 0 and \
#                 self.__options & AnalysisTask.OPTION_LOAD_DUMP_ALL != 0:
#             clock_load = Clock()
#             total_result = self.__strategy.load_analysis_report(full_dump_path)
#             print('Load all analysis result finished, Time spending: %ss' % clock_load.elapsed_s())
#         else:
#             total_result = self.__strategy.analysis_advance(
#                 securities_list, self.__analyzer_list, self.__time_serial,
#                 self.__progress_rate,
#                 self.__options & AnalysisTask.OPTION_CALC != 0,
#                 self.__options & AnalysisTask.OPTION_FROM_CACHE != 0, self.__options & AnalysisTask.OPTION_UPDATE_CACHE != 0,
#                 self.__options & AnalysisTask.OPTION_LOAD_JSON != 0, self.__options & AnalysisTask.OPTION_DUMP_JSON != 0,
#                 os.path.join(StockAnalysisSystem().get_project_path(), 'TestData')
#             )
#
#         if self.__options & AnalysisTask.OPTION_DUMP_JSON != 0 and \
#                 self.__options & AnalysisTask.OPTION_LOAD_DUMP_ALL != 0:
#             clock_dump = Clock()
#             name_dict_path = os.path.join(StockAnalysisSystem().get_project_path(),
#                                           'TestData', 'analyzer_names.json')
#             self.__strategy.dump_analysis_report(total_result, full_dump_path)
#             self.__strategy.dump_strategy_name_dict(name_dict_path)
#             print('Dump all analysis result finished, Time spending: %ss' % clock_dump.elapsed_s())
#
#         print('All analysis finished, time spending: %ss' % clock_all.elapsed_s())
#         return total_result
#
#     def fetch_stock_metrics(self) -> pd.DataFrame or None:
#         if self.__options & AnalysisTask.OPTION_ATTACH_BASIC_INDEX == 0:
#             return None
#
#         daily_metrics = None
#         # daily_metrics = self.fetch_metrics_from_web()
#         if not isinstance(daily_metrics, pd.DataFrame) or daily_metrics.empty:
#             print('Fetch daily metrics data fail, use local.')
#             daily_metrics = self.fetch_metrics_from_local()
#
#         if not isinstance(daily_metrics, pd.DataFrame) or daily_metrics.empty:
#             print('No metrics data.')
#             return None
#
#         if '_id' in daily_metrics.columns:
#             del daily_metrics['_id']
#         if 'trade_date' in daily_metrics.columns:
#             del daily_metrics['trade_date']
#
#         daily_metrics.columns = self.__data_hub.get_data_center().fields_to_readable(list(daily_metrics.columns))
#
#         return daily_metrics
#
#     def fetch_metrics_from_web(self) -> pd.DataFrame or None:
#         trade_calender = self.__data_hub.get_data_center().query_from_plugin('Market.TradeCalender', exchange='SSE',
#                                                                              trade_date=(days_ago(30), now()))
#         if not isinstance(trade_calender, pd.DataFrame) or trade_calender.empty:
#             print('Fetch trade calender from web fail.')
#             return None
#
#         trade_calender = trade_calender[trade_calender['status'] == 1]
#         trade_calender = trade_calender.sort_values('trade_date', ascending=False)
#         last_trade_date = trade_calender.iloc[1]['trade_date']
#
#         daily_metrics = self.__data_hub.get_data_center().query_from_plugin(
#             'Metrics.Stock.Daily', trade_date=(last_trade_date, last_trade_date))
#         return daily_metrics
#
#     def fetch_metrics_from_local(self) -> pd.DataFrame or None:
#         agent = self.__data_hub.get_data_center().get_data_agent('Metrics.Stock.Daily')
#         if agent is None:
#             print('No data agent for Metrics.Stock.Daily')
#             return None
#         since, until = agent.data_range('Metrics.Stock.Daily')
#         if until is None:
#             print('No local metrics data.')
#         daily_metrics = self.__data_hub.get_data_center().query_from_local('Metrics.Stock.Daily',
#                                                                            trade_date=(until, until))
#         return daily_metrics
#
#     def gen_report(self, result_list: [AnalysisResult], stock_metrics: pd.DataFrame or None):
#         clock = Clock()
#         self.__strategy.generate_report_excel_common(result_list, self.__report_path, stock_metrics)
#         print('Generate report time spending: %ss' % str(clock.elapsed_s()))
#
#
# # ---------------------------------------------------- AnalyzerUi ----------------------------------------------------

class AnalyzerUi(QWidget):
    # task_finish_signal = pyqtSignal()

    TABLE_HEADER_SELECTOR = ['', 'Selector', 'Comments', 'UUID', 'Status']
    TABLE_HEADER_ANALYZER = ['', 'Strategy', 'Comments', 'UUID', 'Status']

    def __init__(self, context: UiContext):
        super(AnalyzerUi, self).__init__()

        self.__context = context

        self.__analyzer_info = []

        # Thread and task related
        self.__selector_list = []
        self.__analyzer_list = []
        self.__result_output = os.getcwd()
        self.__timing_clock = Clock()
        # self.task_finish_signal.connect(self.__on_task_done)

        # self.__task_res_id = []
        self.__first_post_update = True
        self.__current_update_task = None

        # Timer for update status
        self.__timer = QTimer()
        self.__timer.setInterval(1000)
        self.__timer.timeout.connect(self.on_timer)
        self.__timer.start()

        # UI related
        group, layout = create_v_group_box('Selector')
        self.__group_selector = group
        self.__layout_selector = layout

        group, layout = create_v_group_box('Analyzer')
        self.__group_analyzer = group
        self.__layout_analyzer = layout

        group, layout = create_v_group_box('Option')
        self.__group_option = group
        self.__layout_option = layout

        group, layout = create_h_group_box('Result')
        self.__group_result = group
        self.__layout_result = layout

        self.__table_selector = TableViewEx()
        self.__table_analyzer = TableViewEx()

        # self.__radio_group_selector = QButtonGroup(self)
        # self.__radio_all = QRadioButton('All')
        # self.__radio_tags = QRadioButton('Tags')
        # self.__radio_manual = QRadioButton('Manual')
        # self.__table_preview = QTableWidget()

        self.__check_force_calc = QCheckBox('Force Calc')
        self.__check_auto_cache = QCheckBox('Cache Result')

        self.__check_load_json = QCheckBox('Load Json')
        self.__check_dump_json = QCheckBox('Dump Json')
        self.__check_load_dump_all = QCheckBox('Load/Dump All')

        self.__datetime_time_since = QDateTimeEdit(years_ago(5))
        self.__datetime_time_until = QDateTimeEdit(now())

        self.__edit_path = QLineEdit('analysis_report.xlsx')
        self.__button_browse = QPushButton('Browse')

        self.__button_selector = QPushButton('Selector')
        self.__button_analyzer = QPushButton('Analyzer')
        self.__button_result = QPushButton('Result')
        self.__button_run_strategy = QPushButton('Run Strategy')

        self.__check_attach_basic_index = QCheckBox('Attach Basic Index')

        self.init_ui()
        self.update_selector()
        self.update_analyzer()
        self.post_progress_updater()

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.setMinimumSize(600, 400)

        self.__layout_selector.addWidget(self.__table_selector)
        main_layout.addWidget(self.__group_selector)

        self.__layout_analyzer.addWidget(self.__table_analyzer)
        main_layout.addWidget(self.__group_analyzer)

        self.__layout_result.addWidget(self.__edit_path)
        self.__layout_result.addWidget(self.__button_browse)
        main_layout.addWidget(self.__group_result)

        grid_layout = QGridLayout()
        grid_layout.addWidget(self.__check_force_calc, 0, 0)
        grid_layout.addWidget(self.__check_auto_cache, 1, 0)
        grid_layout.addWidget(self.__check_load_json, 0, 1)
        grid_layout.addWidget(self.__check_dump_json, 1, 1)

        grid_layout.addWidget(QLabel(' '), 0, 2)
        grid_layout.addWidget(QLabel(' '), 0, 2)

        grid_layout.addWidget(QLabel('Since'), 0, 3)
        grid_layout.addWidget(QLabel('Until'), 1, 3)
        grid_layout.addWidget(self.__datetime_time_since, 0, 4)
        grid_layout.addWidget(self.__datetime_time_until, 1, 4)

        grid_layout.addWidget(self.__check_attach_basic_index, 2, 0, 3, 1)
        grid_layout.addWidget(self.__check_load_dump_all, 2, 1, 3, 1)

        self.__layout_option.addLayout(grid_layout)

        main_layout.addWidget(self.__group_option)

        bottom_control_area = QHBoxLayout()
        main_layout.addLayout(bottom_control_area)

        bottom_control_area.addWidget(QLabel('Strategy Flow: '), 99)
        bottom_control_area.addWidget(self.__button_selector)
        bottom_control_area.addWidget(QLabel('==>'))
        bottom_control_area.addWidget(self.__button_analyzer)
        bottom_control_area.addWidget(QLabel('==>'))
        bottom_control_area.addWidget(self.__button_result)
        bottom_control_area.addWidget(QLabel(' | '))
        bottom_control_area.addWidget(self.__button_run_strategy)

    def __config_control(self):
        self.__table_selector.SetCheckableColumn(0)
        self.__table_selector.SetColumn(AnalyzerUi.TABLE_HEADER_SELECTOR)
        self.__table_selector.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.__table_analyzer.SetCheckableColumn(0)
        self.__table_analyzer.SetColumn(AnalyzerUi.TABLE_HEADER_ANALYZER)
        self.__table_analyzer.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.__check_auto_cache.setChecked(True)
        self.__datetime_time_since.setCalendarPopup(True)
        self.__datetime_time_until.setCalendarPopup(True)

        self.__check_force_calc.setToolTip('勾选此项后，程序将不会从缓存中读取分析结果，并强制进行实时计算。')
        self.__check_auto_cache.setToolTip('勾选此项后，程序会自动缓存分析结果到SasCache数据库')
        self.__check_load_json.setToolTip('仅供Debug：从JSON文件中载入分析结果')
        self.__check_dump_json.setToolTip('仅供Debug：将分析结果写入JSON文件中')
        self.__check_load_dump_all.setToolTip('仅供Debug：载入/保存所有结果而不是按Analyzer分别载入/保存')

        self.__layout_selector.setSpacing(0)
        self.__layout_analyzer.setSpacing(0)
        self.__layout_option.setSpacing(0)
        self.__layout_result.setSpacing(0)
        self.__layout_selector.setContentsMargins(0, 0, 0, 0)
        self.__layout_analyzer.setContentsMargins(0, 0, 0, 0)
        # self.__layout_result.setContentsMargins(0, 0, 0, 0)

        self.__button_result.clicked.connect(self.on_button_browse)
        self.__button_browse.clicked.connect(self.on_button_browse)
        self.__button_selector.clicked.connect(self.on_button_selector)
        self.__button_analyzer.clicked.connect(self.on_button_analyzer)
        self.__button_run_strategy.clicked.connect(self.on_button_run_strategy)

    def on_button_browse(self):
        file_path, ok = QFileDialog.getSaveFileName(self, 'Select Result Excel Path', '',
                                                    'XLSX Files (*.xlsx);;All Files (*)')
        if ok:
            self.__edit_path.setText(file_path)

    def on_button_selector(self):
        self.__group_selector.setVisible(True)
        self.__group_analyzer.setVisible(not self.__group_analyzer.isVisible())

    def on_button_analyzer(self):
        self.__group_analyzer.setVisible(True)
        self.__group_selector.setVisible(not self.__group_selector.isVisible())

    def on_button_run_strategy(self):
        selector_list = []
        analyzer_list = []

        output_path = self.__edit_path.text()
        if len(output_path.strip()) == 0:
            QMessageBox.information(self,
                                    QtCore.QCoreApplication.translate('', '配置缺失'),
                                    QtCore.QCoreApplication.translate('', '请指定结果输出文件'),
                                    QMessageBox.Close, QMessageBox.Close)

        for i in range(self.__table_analyzer.RowCount()):
            if self.__table_analyzer.GetItemCheckState(i, 0) == QtCore.Qt.Checked:
                uuid = self.__table_analyzer.GetItemText(i, 3)
                analyzer_list.append(uuid)

        if len(analyzer_list) == 0:
            QMessageBox.information(None, '提示', '请至少选择一个分析方法')
            return

        self.__selector_list = selector_list
        self.__analyzer_list = analyzer_list
        self.__result_output = output_path

        self.execute_update()

    def on_timer(self):
        if self.__current_update_task is None or self.__current_update_task.working():
            return

        total_progress = ProgressRate()
        updater: ResourceTagUpdater = self.__current_update_task.get_updater()
        updated_res_id = updater.get_resource_ids()

        done_progress = []
        for res_id in updated_res_id:
            progress: ProgressRate = updater.get_resource(res_id, 'progress')
            if progress is None:
                continue
            total_progress.combine_with(progress)
            if progress.progress_done():
                done_progress.append(res_id)

        for i in range(self.__table_analyzer.RowCount()):
            uuid = self.__table_analyzer.GetItemText(i, 3)
            if total_progress.has_progress(uuid):
                rate = total_progress.get_progress_rate(uuid)
                self.__table_analyzer.SetItemText(i, 4, '%.2f%%' % (rate * 100))
            else:
                self.__table_analyzer.SetItemText(i, 4, '')

        if len(updated_res_id) > 0:
            if len(done_progress) != len(updated_res_id):
                self.post_progress_updater()
            else:
                self.__context.get_sas_interface().sas_delete_resource(done_progress)
                self.__current_update_task = None
                # If progress done at process startup, do not pop up message box
                if not self.__first_post_update:
                    self.__on_analysis_done()
                self.__first_post_update = False

    # def closeEvent(self, event):
    #     if self.__task_thread is not None:
    #         QMessageBox.information(self,
    #                                 QtCore.QCoreApplication.translate('', '无法关闭窗口'),
    #                                 QtCore.QCoreApplication.translate('', '策略运行过程中无法关闭此窗口'),
    #                                 QMessageBox.Close, QMessageBox.Close)
    #         event.ignore()
    #     else:
    #         event.accept()

    # --------------------------------------------------------------------------------------

    def update_selector(self):
        self.__table_selector.Clear()
        self.__table_selector.SetRowCount(0)
        self.__table_selector.SetColumn(AnalyzerUi.TABLE_HEADER_SELECTOR)

        self.__table_selector.AppendRow(['', '所有股票', '当前只支持所有股票，不选默认也是所有股票', '-'])

        # Add check box
        # check_item = QTableWidgetItem()
        # check_item.setCheckState(QtCore.Qt.Unchecked)
        # self.__table_selector.setItem(0, 0, check_item)

    def update_analyzer(self):
        self.__table_analyzer.Clear()
        self.__table_analyzer.SetRowCount(0)
        self.__table_analyzer.SetColumn(AnalyzerUi.TABLE_HEADER_ANALYZER)

        self.__analyzer_info = self.__context.get_sas_interface().sas_get_analyzer_probs()

        # if len(self.__analyzer_info) == 0:
        #     self.__analyzer_info = self.__context.get_sas_interface().sas_get_analyzer_probs()
        #

        for prob in self.__analyzer_info:
            line = [
                '',             # Place holder for check box
                prob.get('name', ''),
                prob.get('detail', ''),
                prob.get('uuid', ''),
                '',             # Place holder for status
                ]
            self.__table_analyzer.AppendRow(line)
            # index = self.__table_analyzer.RowCount() - 1

            # Add check box
            # check_item = QTableWidgetItem()
            # check_item.setCheckState(QtCore.Qt.Unchecked)
            # self.__table_analyzer.setItem(index, 0, check_item)

    # --------------------------------------------------------------------------

    # def load_analyzer_info(self) -> [(str, str, str)]:
    #     info = []
    #     probs = self.__strategy_entry.strategy_prob()
    #     for prob in probs:
    #         methods = prob.get('methods', [])
    #         for method in methods:
    #             method_uuid = method[0]
    #             method_name = method[1]
    #             method_detail = method[2]
    #             method_entry = method[3]
    #             if method_entry is not None and '测试' not in method_name:
    #                 # Notice the item order
    #                 info.append([method_uuid, method_name, method_detail])
    #     return info

    # --------------------------------- Thread ---------------------------------

    def execute_update(self):
        # options = AnalysisTask.OPTION_CALC
        #
        # if not self.__check_force_calc.isChecked():
        #     options |= AnalysisTask.OPTION_FROM_CACHE
        #
        # if self.__check_auto_cache.isChecked():
        #     options |= AnalysisTask.OPTION_UPDATE_CACHE
        #
        # if self.__check_load_json.isChecked():
        #     options |= AnalysisTask.OPTION_LOAD_JSON
        # if self.__check_dump_json.isChecked():
        #     options |= AnalysisTask.OPTION_DUMP_JSON
        # if self.__check_load_dump_all.isChecked():
        #     options |= AnalysisTask.OPTION_LOAD_DUMP_ALL
        #
        # if self.__check_attach_basic_index.isChecked():
        #     options |= AnalysisTask.OPTION_ATTACH_BASIC_INDEX

        time_serial = (to_py_datetime(self.__datetime_time_since.dateTime()),
                       to_py_datetime(self.__datetime_time_until.dateTime()))

        # self.__timing_clock.reset()
        # task = AnalysisTask(self, self.__strategy_entry, self.__data_hub_entry,
        #                     self.__selector_list, self.__analyzer_list, time_serial,
        #                     options, self.__result_output, self.__progress_rate)
        # StockAnalysisSystem().get_task_queue().append_task(task)

        securities = self.__context.get_sas_interface().sas_get_stock_identities()
        self.__context.get_sas_interface().sas_execute_analysis(
            securities, self.__analyzer_list, time_serial,
            enable_from_cache=not self.__check_force_calc.isChecked(),
            enable_update_cache=self.__check_auto_cache.isChecked(),
            debug_load_json=self.__check_load_json.isChecked() or self.__check_load_dump_all.isChecked(),
            debug_dump_json=self.__check_dump_json.isChecked() or self.__check_load_dump_all.isChecked(),
            dump_path=self.__result_output,
            attach_basic_index=self.__check_attach_basic_index.isChecked(),
            generate_report=True,           # The report will be generated on server side.
        )
        self.post_progress_updater()
        # self.__task_res_id.append(res_id)
        # self.__context.get_res_sync().add_sync_resource(res_id, 'progress')

        # if self.__task_thread is None:
        #     self.__task_thread = threading.Thread(target=self.ui_task)
        #     StockAnalysisSystem().lock_sys_quit()
        #     self.__timing_clock.reset()
        #     self.__task_thread.start()
        # else:
        #     print('Task already running...')
        #     QMessageBox.information(self,
        #                             QtCore.QCoreApplication.translate('', '无法执行'),
        #                             QtCore.QCoreApplication.translate('', '已经有策略在运行中，无法同时运行多个策略'),
        #                             QMessageBox.Close, QMessageBox.Close)

    # def ui_task(self):
    #     print('Strategy task start.')
    #
    #     self.__lock.acquire()
    #     selector_list = self.__selector_list
    #     analyzer_list = self.__analyzer_list
    #     output_path = self.__result_output
    #     self.__lock.release()
    #
    #     data_utility = self.__data_hub_entry.get_data_utility()
    #     stock_list = data_utility.get_stock_identities()
    #
    #     self.__progress_rate.reset()
    #
    #     # ------------- Run analyzer -------------
    #     clock = Clock()
    #
    #     # result = self.__strategy_entry.run_strategy(stock_list, analyzer_list, progress=self.__progress_rate)
    #
    #     total_result = []
    #     uncached_analyzer = []
    #
    #     for analyzer in analyzer_list:
    #         result = self.__strategy_entry.result_from_cache('Result.Analyzer', analyzer=analyzer)
    #         if result is None or len(result) == 0:
    #             uncached_analyzer.append(analyzer)
    #             result = self.__strategy_entry.run_strategy(stock_list, [analyzer], progress=self.__progress_rate)
    #         else:
    #             self.__progress_rate.finish_progress(analyzer)
    #         if result is not None and len(result) > 0:
    #             total_result.extend(result)
    #
    #     # DEBUG: Load result from json file
    #     # result = None
    #     # with open('analysis_result.json', 'rt') as f:
    #     #     result = analysis_results_from_json(f)
    #     # if result is None:
    #     #     return
    #
    #     print('Analysis time spending: ' + str(clock.elapsed_s()) + ' s')
    #
    #     # # DEBUG: Dump result to json file
    #     # with open('analysis_result.json', 'wt') as f:
    #     #     analysis_results_to_json(result, f)
    #
    #     # self.__strategy_entry.cache_analysis_result('Result.Analyzer', result)
    #     result2 = self.__strategy_entry.result_from_cache('Result.Analyzer')
    #     print(result2)
    #
    #     result = analysis_result_dataframe_to_list(result2)
    #     print(result)
    #
    #     # ------------ Parse to Table ------------
    #
    #     result_table = analysis_result_list_to_analyzer_security_table(result)
    #
    #     # ----------- Generate report ------------
    #     clock.reset()
    #     stock_list = self.__data_hub_entry.get_data_utility().get_stock_list()
    #     stock_dict = {_id: _name for _id, _name in stock_list}
    #     name_dict = self.__strategy_entry.strategy_name_dict()
    #     generate_analysis_report(result_table, output_path, name_dict, stock_dict)
    #     print('Generate report time spending: ' + str(clock.elapsed_s()) + ' s')
    #
    #     # ----------------- End ------------------
    #     self.task_finish_signal.emit()
    #     print('Update task finished.')

    # ---------------------------------------------------------------------------------

    # def notify_task_done(self):
    #     self.task_finish_signal.emit()

    # def __on_task_done(self):
    #     # StockAnalysisSystem().release_sys_quit()
    #     QMessageBox.information(self,
    #                             QtCore.QCoreApplication.translate('main', '远行完成'),
    #                             QtCore.QCoreApplication.translate('main', '策略运行完成，耗时' +
    #                                                               str(self.__timing_clock.elapsed_s()) + '秒\n' +
    #                                                               '报告生成路径：' + self.__result_output),
    #                             QMessageBox.Ok, QMessageBox.Ok)
        
    def __on_analysis_done(self):
        QMessageBox.information(self,
                                QtCore.QCoreApplication.translate('main', '分析完成'),
                                QtCore.QCoreApplication.translate('main', '策略运行完成，耗时' +
                                                                  str(self.__timing_clock.elapsed_s()) + '秒\n' +
                                                                  '请到服务目录下获取analysis_report.xlsx'),
                                QMessageBox.Ok, QMessageBox.Ok)

    def post_progress_updater(self):
        updater = ResourceTagUpdater(self.__context.get_sas_interface(), 'Analysis Progress Updater')
        updater.set_resource_tags('analysis_task')
        updater.set_update_resource_keys('progress')

        update_task = ResourceUpdateTask(updater)
        self.__context.get_task_queue().append_task(update_task)
        self.__current_update_task = update_task


# ----------------------------------------------------------------------------------------------------------------------

def main():
    from StockAnalysisSystem.interface.interface_local import LocalInterface

    project_path = os.path.dirname(os.path.dirname(os.getcwd()))

    local_if = LocalInterface()
    local_if.if_init(project_path=project_path)

    context = UiContext()
    context.set_sas_interface(local_if)

    app = QApplication(sys.argv)
    dlg = WrapperQDialog(AnalyzerUi(context))
    dlg.exec()


# ----------------------------------------------------------------------------------------------------------------------

def exception_hook(type, value, tback):
    # log the exception here
    print('Exception hook triggered.')
    print(type)
    print(value)
    print(tback)
    # then call the default handler
    sys.__excepthook__(type, value, tback)


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






































