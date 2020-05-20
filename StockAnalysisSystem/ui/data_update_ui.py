#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2017/08/08
@file: data_update.py
@function:
@modify:
"""
import copy
import traceback
import threading

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import QHeaderView
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Executor

from ..core.DataHubEntry import *
from ..core.Utiltity.common import *
from ..core.Utiltity.ui_utility import *
from ..core.Utiltity.task_queue import *
from ..core.Utiltity.TableViewEx import *
from ..core.Database.UpdateTableEx import *
from ..core.StockAnalysisSystem import StockAnalysisSystem


DEFAULT_INFO = """数据更新界面说明：
1. 要使用此功能，首先请在设置界面配置好TS_TOKEN及NOSQL相关设置项目
2. 如果从零开始，请先更新Market.SecuritiesInfo以获取股票列表，后续更新方可正常运作
3. 由于采集本地数据范围需要从数据库中读取大量数据，故界面刷新会较慢，后续会对此进行优化
4. 在首页更新财务信息会对所有股票执行一次，故耗时非常长，请做好挂机准备
5. Force Update会拉取从1990年至今的数据，耗时非常长，请谨慎使用"""


# ---------------------------------- UpdateTask ----------------------------------

class UpdateTask(TaskQueue.Task):
    def __init__(self, ui, data_hub, data_center, force: bool):
        super(UpdateTask, self).__init__('UpdateTask')
        self.__ui = ui
        self.__force = force
        self.__data_hub = data_hub
        self.__data_center = data_center
        self.__quit = False

        # Thread pool
        self.__patch_count = 0
        self.__apply_count = 0
        self.__future = None
        self.__pool = ThreadPoolExecutor(max_workers=1)

        # Parameters
        self.agent = None
        self.identities = []
        self.clock = Clock(False)
        self.progress = ProgressRate()

    def in_work_package(self, uri: str) -> bool:
        return self.agent.adapt(uri)

    def set_work_package(self, agent: DataAgent, identities: list or str or None):
        if isinstance(identities, str):
            identities = [identities]
        self.identities = identities
        self.agent = agent

    def run(self):
        print('Update task start.')

        self.__patch_count = 0
        self.__apply_count = 0
        try:
            # Catch "pymongo.errors.ServerSelectionTimeoutError: No servers found yet" exception and continue.
            self.__execute_update()
        except Exception as e:
            print('Update got Exception: ')
            print(e)
            print(traceback.format_exc())
            print('Continue...')
        finally:
            if self.__future is not None:
                self.__future.cancel()
        print('Update task finished.')

    def quit(self):
        self.__quit = True

    def identity(self) -> str:
        return self.agent.base_uri() if self.agent is not None else ''

    # ------------------------------------- Task -------------------------------------

    def __execute_update(self):
        # Get identities here to ensure we can get the new list after stock info updated
        update_list = self.identities if self.identities is not None and len(self.identities) > 0 else \
                      self.agent.update_list()
        if update_list is None or len(update_list) == 0:
            update_list = [None]
        progress = len(update_list)

        self.clock.reset()
        self.progress.reset()
        self.progress.set_progress(self.agent.base_uri(), 0, progress)

        for identity in update_list:
            while (self.__patch_count - self.__apply_count > 20) and not self.__quit:
                time.sleep(0.5)
                continue
            if self.__quit:
                break

            print('------------------------------------------------------------------------------------')

            if identity is not None:
                # Optimise: Update not earlier than listing date.
                listing_date = self.__data_hub.get_data_utility().get_securities_listing_date(identity, default_since())

                if self.__force:
                    since, until = listing_date, now()
                else:
                    since, until = self.__data_center.calc_update_range(self.agent.base_uri(), identity)
                    since = max(listing_date, since)
                time_serial = (since, until)
            else:
                time_serial = None

            patch = self.__data_center.build_local_data_patch(
                self.agent.base_uri(), identity, time_serial, force=self.__force)
            self.__patch_count += 1
            print('Patch count: ' + str(self.__patch_count))

            self.__future = self.__pool.submit(self.__execute_persistence,
                                               self.agent.base_uri(), identity, patch)

        if self.__future is not None:
            print('Waiting for persistence task finish...')
            self.__future.result()
        self.clock.freeze()
        # self.__ui.task_finish_signal[UpdateTask].emit(self)

    def __execute_persistence(self, uri: str, identity: str, patch: tuple) -> bool:
        try:
            if patch is not None:
                self.__data_center.apply_local_data_patch(patch)
            if identity is not None:
                self.progress.set_progress([uri, identity], 1, 1)
            self.progress.increase_progress(uri)
        except Exception as e:
            print('e')
            return False
        finally:
            self.__apply_count += 1
            print('Persistence count: ' + str(self.__apply_count))
        return True


# ---------------------------------- RefreshTask ----------------------------------

class RefreshTask(TaskQueue.Task):
    def __init__(self, ui):
        super(RefreshTask, self).__init__('RefreshTask')
        self.__ui = ui

    def run(self):
        print('Refresh task start.')
        self.__ui.update_table_content()
        self.__ui.refresh_finish_signal.emit()
        print('Refresh task finished.')

    def identity(self) -> str:
        return 'RefreshTask'


# ------------------------------ UpdateStockListTask ------------------------------

class UpdateStockListTask(TaskQueue.Task):
    def __init__(self, data_utility):
        super(UpdateStockListTask, self).__init__('UpdateStockListTask')
        self.__data_utility = data_utility

    def run(self):
        print('Update stock list task start.')
        self.__data_utility.refresh_cache()
        print('Update stock list task finished.')

    def identity(self) -> str:
        return 'UpdateStockListTask'


# ---------------------------------------------------- DataUpdateUi ----------------------------------------------------

class DataUpdateUi(QWidget, TaskQueue.Observer):
    task_finish_signal = pyqtSignal([UpdateTask])
    refresh_finish_signal = pyqtSignal()

    INDEX_CHECK = 0
    INDEX_ITEM = 1
    INDEX_STATUS = 8
    TABLE_HEADER = ['', 'Item', 'Local Data Since', 'Local Data Until', 'Latest Update',
                    'Update Estimation', 'Sub Update', 'Update', 'Status']

    def get_uri_sub_update(self, uri: str) -> list or None:
        agent = self.__data_hub.get_data_center().get_data_agent(uri)
        if agent is not None:
            return agent.update_list()
        else:
            print('Error: Agent of URI %s is None.' % uri)

    def __init__(self, data_hub_entry: DataHubEntry, update_table: UpdateTableEx):
        super(DataUpdateUi, self).__init__()

        # Access entry
        self.__data_hub = data_hub_entry
        self.__data_center = self.__data_hub.get_data_center()
        self.__update_table = update_table

        # Table content
        self.__display_uri = []
        self.__display_identities = None
        self.__display_table_lines = []

        # Page related
        self.__page = 0
        self.__item_per_page = 20

        # For processing updating
        self.__processing_update_tasks = []
        # Fot task counting
        self.__processing_update_tasks_count = []

        self.task_finish_signal.connect(self.__on_task_done)
        self.refresh_finish_signal.connect(self.update_table_display)

        # Timer for update status
        self.__timer = QTimer()
        self.__timer.setInterval(1000)
        self.__timer.timeout.connect(self.on_timer)
        self.__timer.start()

        # UI related
        self.__info_panel = QLabel(DEFAULT_INFO)

        self.__table_main = TableViewEx()
        self.__button_head_page = QPushButton('<<')
        self.__button_prev_page = QPushButton('<')
        self.__button_next_page = QPushButton('>')
        self.__button_tail_page = QPushButton('>>')
        self.__button_upper_level = QPushButton('↑')

        self.__button_refresh = QPushButton('Refresh')
        self.__button_batch_auto_update = QPushButton('Auto Update Select')
        self.__button_batch_force_update = QPushButton('Force Update Select')

        self.init_ui()

        # Post update and cache stock list after posting RefreshTask
        data_utility = self.__data_hub.get_data_utility()
        StockAnalysisSystem().get_task_queue().add_observer(self)
        StockAnalysisSystem().get_task_queue().append_task(UpdateStockListTask(data_utility))

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()
        self.__to_top_level()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.setMinimumSize(600, 400)
        main_layout.addWidget(self.__table_main)

        bottom_control_area = QHBoxLayout()
        main_layout.addLayout(bottom_control_area)

        bottom_right_area = QVBoxLayout()
        bottom_control_area.addWidget(self.__info_panel, 99)
        bottom_control_area.addLayout(bottom_right_area, 0)

        line = horizon_layout([self.__button_head_page, self.__button_prev_page,
                               self.__button_next_page, self.__button_tail_page,
                               self.__button_upper_level, self.__button_refresh])
        bottom_right_area.addLayout(line)

        line = horizon_layout([self.__button_batch_auto_update, self.__button_batch_force_update])
        bottom_right_area.addLayout(line)

    def __config_control(self):
        self.__table_main.SetColumn(DataUpdateUi.TABLE_HEADER)
        self.__table_main.SetCheckableColumn(DataUpdateUi.INDEX_CHECK)
        self.__table_main.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.__button_head_page.clicked.connect(partial(self.on_page_control, '<<'))
        self.__button_prev_page.clicked.connect(partial(self.on_page_control, '<'))
        self.__button_next_page.clicked.connect(partial(self.on_page_control, '>'))
        self.__button_tail_page.clicked.connect(partial(self.on_page_control, '>>'))
        self.__button_upper_level.clicked.connect(partial(self.on_page_control, '^'))
        self.__button_refresh.clicked.connect(partial(self.on_page_control, 'r'))

        self.__button_batch_auto_update.clicked.connect(partial(self.on_batch_update, False))
        self.__button_batch_force_update.clicked.connect(partial(self.on_batch_update, True))

    def on_detail_button(self, uri: str):
        print('Detail of ' + uri)
        self.__page = 0
        self.__to_detail_level(uri)

    def on_auto_update_button(self, uri: str, identity: str):
        print('Auto update ' + uri + ':' + str(identity))
        self.__build_post_update_task(uri, identity, False)

    def on_force_update_button(self, uri: str, identity: str):
        print('Force update ' + uri + ' : ' + str(identity))
        self.__build_post_update_task(uri, identity, True)

    def on_batch_update(self, force: bool):
        for i in range(self.__table_main.RowCount()):
            if self.__table_main.GetItemCheckState(i, DataUpdateUi.INDEX_CHECK) == Qt.Checked:
                item_id = self.__table_main.GetItemText(i, DataUpdateUi.INDEX_ITEM)
                # A little ugly...To distinguish it's uri or securities ideneity
                if self.__display_identities is None:
                    self.__build_post_update_task(item_id, None, force)
                else:
                    self.__build_post_update_task(self.__display_uri[0], item_id, force)

    def on_page_control(self, control: str):
        # data_utility = self.__data_hub.get_data_utility()
        # stock_list = data_utility.get_stock_list()
        # max_page = len(stock_list) // self.__item_per_page

        if self.__display_identities is None:
            max_item_count = len(self.__display_uri)
        else:
            max_item_count = len(self.__display_identities)
        max_page = max_item_count // self.__item_per_page

        new_page = self.__page
        if control == '<<':
            new_page = 0
        elif control == '<':
            new_page = max(self.__page - 1, 0)
        elif control == '>':
            new_page = min(self.__page + 1, max_page)
        elif control == '>>':
            new_page = max_page
        elif control == '^':
            self.__to_top_level()

        if control in ['<<', '<', '>', '>>', 'r']:
            if control == 'r' or new_page != self.__page:
                self.update_table()
                self.__page = new_page

    def on_timer(self):
        for i in range(self.__table_main.RowCount()):
            item_id = self.__table_main.GetItemText(i, DataUpdateUi.INDEX_ITEM)
            # A little ugly...To distinguish it's uri or securities identity
            if self.__display_identities is None:
                uri = item_id
                prog_id = uri
            else:
                uri = self.__display_uri[0]
                prog_id = [uri, item_id]
            for task in self.__processing_update_tasks:
                if not task.in_work_package(uri):
                    continue
                text = []
                if task.status() in [TaskQueue.Task.STATUS_IDLE, TaskQueue.Task.STATUS_PENDING]:
                    text.append('等待中...')
                else:
                    if task.progress.has_progress(prog_id):
                        rate = task.progress.get_progress_rate(prog_id)
                        text.append('%ss' % task.clock.elapsed_s())
                        text.append('%.2f%%' % (rate * 100))
                    if task.status() == TaskQueue.Task.STATUS_CANCELED:
                        text.append('[Canceled]')
                    elif task.status() == TaskQueue.Task.STATUS_FINISHED:
                        text.append('[Finished]')
                    elif task.status() == TaskQueue.Task.STATUS_EXCEPTION:
                        text.append('[Error]')
                self.__table_main.SetItemText(i, DataUpdateUi.INDEX_STATUS, ' | '.join(text))
                break

    # def closeEvent(self, event):
    #     if self.__task_thread is not None:
    #         QMessageBox.information(self,
    #                                 QtCore.QCoreApplication.translate('', '无法关闭窗口'),
    #                                 QtCore.QCoreApplication.translate('', '更新过程中无法关闭此窗口'),
    #                                 QMessageBox.Close, QMessageBox.Close)
    #         event.ignore()
    #     else:
    #         event.accept()

    # ---------------------------------------- Table Update ----------------------------------------

    def update_table(self):
        self.__table_main.Clear()
        self.__table_main.SetColumn(DataUpdateUi.TABLE_HEADER)
        self.__table_main.AppendRow(['', '刷新中...', '', '', '', '', '', '', ''])
        task = RefreshTask(self)
        StockAnalysisSystem().get_task_queue().append_task(task)

    def update_table_display(self):
        self.__table_main.Clear()
        self.__table_main.SetColumn(DataUpdateUi.TABLE_HEADER)

        for line in self.__display_table_lines:
            self.__table_main.AppendRow(line)
            index = self.__table_main.RowCount() - 1

            # Add detail button
            # Only if currently in top level
            if self.__display_identities is None or len(self.__display_identities) == 0:
                uri = line[1]
                agent = self.__data_center.get_data_agent(uri)
                if agent is not None and len(agent.update_list()) > 0:
                    button = QPushButton('Enter')
                    button.clicked.connect(partial(self.on_detail_button, line[1]))
                    self.__table_main.SetCellWidget(index, 6, button)

            # Add update button
            button_auto = QPushButton('Auto')
            button_force = QPushButton('Force')
            if self.__display_identities is None:
                button_auto.clicked.connect(partial(self.on_auto_update_button, line[1], None))
                button_force.clicked.connect(partial(self.on_force_update_button, line[1], None))
            else:
                button_auto.clicked.connect(partial(self.on_auto_update_button, self.__display_uri[0], line[1]))
                button_force.clicked.connect(partial(self.on_force_update_button, self.__display_uri[0], line[1]))
            self.__table_main.SetCellWidget(index, 7, [button_auto, button_force])

    def update_table_content(self):
        contents = []
        count = self.__item_per_page
        offset = self.__page * self.__item_per_page

        for uri in self.__display_uri:
            update_details = self.__display_identities if \
                self.__display_identities is not None else [None]
            for index in range(offset, offset + count):
                if index >= len(update_details):
                    break
                line = self.generate_line_content(uri, update_details[index])
                if line is not None:
                    contents.append(line)
        self.__display_table_lines = contents

    def generate_line_content(self, uri: str, identity: str or None) -> [list] or None:
        line = []

        agent = self.__data_center.get_data_agent(uri)
        update_table = self.__update_table

        if agent is None:
            return None

        update_tags = uri.split('.') + ([identity] if identity is not None else [])
        since, until = update_table.get_since_until(update_tags)
        
        if since is None or until is None:
            # TODO: Workaround - because each stock storage in each table.
            # So we cannot fetch its time range with this method.
            since, until = agent.data_range(uri, identity)
        if until is not None:
            update_since = min(tomorrow_of(until), now())
            update_until = now()
        else:
            update_since, update_until = self.__data_center.calc_update_range(uri, identity)

        update_tags = uri.split('.')
        latest_update = self.__update_table.get_last_update_time(update_tags)

        line.append('')     # Place holder for check box
        line.append(identity if str_available(identity) else uri)
        line.append(date2text(since) if since is not None else ' - ')
        line.append(date2text(until) if until is not None else ' - ')
        line.append(date2text(latest_update) if latest_update is not None else ' - ')

        if update_since is not None and update_until is not None:
            line.append(date2text(update_since) + ' - ' + date2text(update_until))
        else:
            line.append(' - ')
        line.append('-')    # Place holder for detail button
        line.append('')     # Place holder for update button
        line.append('')     # Place holder for status

        return line

    # --------------------------------------------------------------------------

    def __to_top_level(self):
        # Temporary exclude Factor related data
        support_uri = self.__data_center.get_all_uri()
        self.__display_uri = [uri for uri in support_uri if 'Factor' not in uri]
        self.__display_identities = None
        self.__page = 0
        self.update_table()

    def __to_detail_level(self, uri: str):
        self.__display_uri = [uri]
        self.__display_identities = self.get_uri_sub_update(uri)
        self.__page = 0
        self.update_table()

    def __build_post_update_task(self, uri: str, identities: list or None, force: bool) -> bool:
        agent = self.__data_center.get_data_agent(uri)
        task = UpdateTask(self, self.__data_hub, self.__data_center, force)
        task.set_work_package(agent, identities)
        self.__processing_update_tasks.append(task)
        self.__processing_update_tasks_count.append(task)
        ret = StockAnalysisSystem().get_task_queue().append_task(task)
        # After updating market info, also update stock list cache
        if ret and (uri == 'Market.SecuritiesInfo' or uri == 'Market.IndexInfo'):
            data_utility = self.__data_hub.get_data_utility()
            StockAnalysisSystem().get_task_queue().append_task(UpdateStockListTask(data_utility))
        return ret

    # ---------------------------------------------------------------------------------

    def on_task_updated(self, task, change: str):
        if change in ['canceled', 'finished']:
            if task in self.__processing_update_tasks_count:
                self.task_finish_signal[UpdateTask].emit(task)

    def __on_task_done(self, task: UpdateTask):
        if task in self.__processing_update_tasks_count:
            self.__processing_update_tasks_count.remove(task)
            print('Finish task: %s, remaining count: %s' % (task.name(), len(self.__processing_update_tasks_count)))
            if len(self.__processing_update_tasks_count) == 0:
                QMessageBox.information(self,
                                        QtCore.QCoreApplication.translate('main', '更新完成'),
                                        QtCore.QCoreApplication.translate('main', '数据更新完成'),
                                        QMessageBox.Ok, QMessageBox.Ok)
                self.__processing_update_tasks.clear()
                self.update_table()
        else:
            print('Impossible: Cannot find finished task in task list.')


# ----------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    data_hub = StockAnalysisSystem().get_data_hub_entry()
    update_table = StockAnalysisSystem().get_database_entry().get_update_table()
    dlg = WrapperQDialog(DataUpdateUi(data_hub, update_table))
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


sys.excepthook = exception_hook


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass

