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
import copy
import traceback
import threading

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import QHeaderView, QLineEdit, QFileDialog, QCheckBox, QDateTimeEdit, QGridLayout, QRadioButton, \
    QButtonGroup

from StockAnalysisSystem.core.AnalyzerEntry import *
from StockAnalysisSystem.core.Utiltity.task_queue import *
from StockAnalysisSystem.core.Utiltity.ui_utility import *
from StockAnalysisSystem.core.Utiltity.TableViewEx import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.AnalyzerUtility import *
from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem


# ------------------------- Analysis Task -------------------------

class AnalysisTask(TaskQueue.Task):
    OPTION_CALC = 1
    OPTION_FROM_CACHE = 2
    OPTION_UPDATE_CACHE = 16
    OPTION_AUTO = OPTION_CALC | OPTION_FROM_CACHE | OPTION_UPDATE_CACHE

    OPTION_FROM_JSON = 1024
    OPTION_DUMP_JSON = 2048

    OPTION_ATTACH_BASIC_INDEX = 4096

    def __init__(self, ui, strategy_entry: StrategyEntry, data_hub: DataHubEntry,
                 selector_list: [str], analyzer_list: [str], time_serial: tuple,
                 options: int, report_path: str, progress_rate: ProgressRate):
        super(AnalysisTask, self).__init__('AnalysisTask')
        self.__ui = ui
        self.__options = options
        self.__data_hub = data_hub
        self.__strategy = strategy_entry
        self.__selector_list = selector_list
        self.__analyzer_list = analyzer_list
        self.__time_serial = time_serial
        self.__report_path = report_path
        self.__progress_rate = progress_rate

    def run(self):
        print('Analysis task start.')

        clock = Clock()
        stock_list = self.select()
        result_list = self.analysis(stock_list)
        stock_metrics = self.fetch_stock_metrics()
        self.gen_report(result_list, stock_metrics)

        print('Analysis task finished, time spending: ' + str(clock.elapsed_s()) + ' s')

        self.__ui.notify_task_done()

    def identity(self) -> str:
        return 'AnalysisTask'

    # -----------------------------------------------------------------------------

    def select(self) -> [str]:
        data_utility = self.__data_hub.get_data_utility()
        stock_list = data_utility.get_stock_identities()
        return stock_list

    def analysis(self, securities_list: [str]) -> [AnalysisResult]:
        clock_all = Clock()
        total_result = self.__strategy.analysis_advance(
            securities_list, self.__analyzer_list, self.__time_serial,
            self.__progress_rate,
            self.__options & AnalysisTask.OPTION_CALC != 0,
            self.__options & AnalysisTask.OPTION_FROM_CACHE != 0, self.__options & AnalysisTask.OPTION_UPDATE_CACHE != 0,
            self.__options & AnalysisTask.OPTION_FROM_JSON != 0, self.__options & AnalysisTask.OPTION_DUMP_JSON != 0,
            os.path.join(StockAnalysisSystem().get_project_path(), 'TestData')
        )
        print('All analysis finished, time spending: %ss' % clock_all.elapsed_s())
        return total_result

    def fetch_stock_metrics(self) -> pd.DataFrame or None:
        if self.__options & AnalysisTask.OPTION_ATTACH_BASIC_INDEX == 0:
            return None

        daily_metrics = None
        # daily_metrics = self.fetch_metrics_from_web()
        if not isinstance(daily_metrics, pd.DataFrame) or daily_metrics.empty:
            print('Fetch daily metrics data fail, use local.')
            daily_metrics = self.fetch_metrics_from_local()

        if not isinstance(daily_metrics, pd.DataFrame) or daily_metrics.empty:
            print('No metrics data.')
            return None

        if '_id' in daily_metrics.columns:
            del daily_metrics['_id']
        if 'trade_date' in daily_metrics.columns:
            del daily_metrics['trade_date']

        daily_metrics.columns = self.__data_hub.get_data_center().fields_to_readable(list(daily_metrics.columns))

        return daily_metrics

    def fetch_metrics_from_web(self) -> pd.DataFrame or None:
        trade_calender = self.__data_hub.get_data_center().query_from_plugin('Market.TradeCalender', exchange='SSE',
                                                                             trade_date=(days_ago(30), now()))
        if not isinstance(trade_calender, pd.DataFrame) or trade_calender.empty:
            print('Fetch trade calender from web fail.')
            return None

        trade_calender = trade_calender[trade_calender['status'] == 1]
        trade_calender = trade_calender.sort_values('trade_date', ascending=False)
        last_trade_date = trade_calender.iloc[1]['trade_date']

        daily_metrics = self.__data_hub.get_data_center().query_from_plugin(
            'Metrics.Stock.Daily', trade_date=(last_trade_date, last_trade_date))
        return daily_metrics

    def fetch_metrics_from_local(self) -> pd.DataFrame or None:
        agent = self.__data_hub.get_data_center().get_data_agent('Metrics.Stock.Daily')
        if agent is None:
            print('No data agent for Metrics.Stock.Daily')
            return None
        since, until = agent.data_range('Metrics.Stock.Daily')
        if until is None:
            print('No local metrics data.')
        daily_metrics = self.__data_hub.get_data_center().query_from_local('Metrics.Stock.Daily',
                                                                           trade_date=(until, until))
        return daily_metrics

    def gen_report(self, result_list: [AnalysisResult], stock_metrics: pd.DataFrame or None):
        clock = Clock()
        self.__strategy.generate_report_excel_common(result_list, self.__report_path, stock_metrics)
        print('Generate report time spending: %ss' % str(clock.elapsed_s()))


# ---------------------------------------------------- AnalyzerUi ----------------------------------------------------

class AnalyzerUi(QWidget):
    task_finish_signal = pyqtSignal()

    TABLE_HEADER_SELECTOR = ['', 'Selector', 'Comments', 'UUID', 'Status']
    TABLE_HEADER_ANALYZER = ['', 'Strategy', 'Comments', 'UUID', 'Status']

    def __init__(self, data_hub_entry: DataHubEntry, strategy_entry: StrategyEntry):
        super(AnalyzerUi, self).__init__()
        self.__data_hub_entry = data_hub_entry
        self.__strategy_entry = strategy_entry

        self.__analyzer_info = self.__strategy_entry.analyzer_info()

        # Thread and task related
        self.__selector_list = []
        self.__analyzer_list = []
        self.__result_output = StockAnalysisSystem().get_project_path()
        self.__timing_clock = Clock()
        self.__progress_rate = ProgressRate()
        self.task_finish_signal.connect(self.__on_task_done)

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

        self.__check_from_json = QCheckBox('From Json')
        self.__check_dump_json = QCheckBox('Dump Json')

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
        grid_layout.addWidget(self.__check_from_json, 0, 1)
        grid_layout.addWidget(self.__check_dump_json, 1, 1)

        grid_layout.addWidget(QLabel(' '), 0, 2)
        grid_layout.addWidget(QLabel(' '), 0, 2)

        grid_layout.addWidget(QLabel('Since'), 0, 3)
        grid_layout.addWidget(QLabel('Until'), 1, 3)
        grid_layout.addWidget(self.__datetime_time_since, 0, 4)
        grid_layout.addWidget(self.__datetime_time_until, 1, 4)

        grid_layout.addWidget(self.__check_attach_basic_index, 2, 0, 3, 1)

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
        self.__check_from_json.setToolTip('仅供Debug：从JSON文件中载入分析结果')
        self.__check_dump_json.setToolTip('仅供Debug：将分析结果写入JSON文件中')

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

        self.execute_update_task()

    def on_timer(self):
        for i in range(self.__table_analyzer.RowCount()):
            uuid = self.__table_analyzer.GetItemText(i, 3)
            if self.__progress_rate.has_progress(uuid):
                rate = self.__progress_rate.get_progress_rate(uuid)
                self.__table_analyzer.SetItemText(i, 4, '%.2f%%' % (rate * 100))
            else:
                self.__table_analyzer.SetItemText(i, 4, '')

    def closeEvent(self, event):
        if self.__task_thread is not None:
            QMessageBox.information(self,
                                    QtCore.QCoreApplication.translate('', '无法关闭窗口'),
                                    QtCore.QCoreApplication.translate('', '策略运行过程中无法关闭此窗口'),
                                    QMessageBox.Close, QMessageBox.Close)
            event.ignore()
        else:
            event.accept()

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

        for method_uuid, method_name, method_detail, _ in self.__analyzer_info:
            line = [
                '',             # Place holder for check box
                method_name,
                method_detail,
                method_uuid,
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

    def execute_update_task(self):
        options = AnalysisTask.OPTION_CALC

        if not self.__check_force_calc.isChecked():
            options |= AnalysisTask.OPTION_FROM_CACHE

        if self.__check_auto_cache.isChecked():
            options |= AnalysisTask.OPTION_UPDATE_CACHE

        if self.__check_from_json.isChecked():
            options |= AnalysisTask.OPTION_FROM_JSON
        if self.__check_dump_json.isChecked():
            options |= AnalysisTask.OPTION_DUMP_JSON

        if self.__check_attach_basic_index.isChecked():
            options |= AnalysisTask.OPTION_ATTACH_BASIC_INDEX

        time_serial = (to_py_datetime(self.__datetime_time_since.dateTime()),
                       to_py_datetime(self.__datetime_time_until.dateTime()))

        task = AnalysisTask(self, self.__strategy_entry, self.__data_hub_entry,
                            self.__selector_list, self.__analyzer_list, time_serial,
                            options, self.__result_output, self.__progress_rate)
        StockAnalysisSystem().get_task_queue().append_task(task)

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
    #     result = analysis_dataframe_to_list(result2)
    #     print(result)
    #
    #     # ------------ Parse to Table ------------
    #
    #     result_table = analysis_result_list_to_table(result)
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

    def notify_task_done(self):
        self.task_finish_signal.emit()

    def __on_task_done(self):
        StockAnalysisSystem().release_sys_quit()
        QMessageBox.information(self,
                                QtCore.QCoreApplication.translate('main', '远行完成'),
                                QtCore.QCoreApplication.translate('main', '策略运行完成，耗时' +
                                                                  str(self.__timing_clock.elapsed_s()) + '秒\n' +
                                                                  '报告生成路径：' + self.__result_output),
                                QMessageBox.Ok, QMessageBox.Ok)


# ----------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    data_hub_entry = StockAnalysisSystem().get_data_hub_entry()
    strategy_entry = StockAnalysisSystem().get_strategy_entry()
    dlg = WrapperQDialog(AnalyzerUi(data_hub_entry, strategy_entry))
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






































