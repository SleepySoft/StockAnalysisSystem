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
import os

from PyQt5.QtCore import QTimer

from StockAnalysisSystem.core.Utility.common import *
from StockAnalysisSystem.core.Utility.task_queue import *
from StockAnalysisSystem.core.Utility.ui_utility import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.Utility.TableViewEx import TableViewEx

from StockAnalysisSystem.ui.Utility.ui_context import UiContext
from StockAnalysisSystem.core.Utility.resource_sync import ResourceTagUpdater, ResourceUpdateTask

DEFAULT_INFO = """数据更新界面说明：
1. 要使用此功能，首先请在设置界面配置好TS_TOKEN及NOSQL相关设置项目
2. 如果从零开始，请先更新Market.SecuritiesInfo以获取股票列表，后续更新方可正常运作
3. 在首页更新财务信息会对所有股票执行一次，故耗时非常长，请做好挂机准备
4. Force Update会拉取从1990年至今的数据，耗时非常长，请谨慎使用"""


# ---------------------------------- UpdateTask ----------------------------------

# class UpdateTask(TaskQueue.Task):
#     def __init__(self, ui, data_hub, data_center, force: bool):
#         super(UpdateTask, self).__init__('UpdateTask')
#         self.__ui = ui
#         self.__force = force
#         self.__data_hub = data_hub
#         self.__data_center = data_center
#         self.__quit = False
# 
#         # Thread pool
#         self.__patch_count = 0
#         self.__apply_count = 0
#         self.__future = None
#         self.__pool = ThreadPoolExecutor(max_workers=1)
# 
#         # Parameters
#         self.agent = None
#         self.identities = []
#         self.clock = Clock(False)
#         self.progress = ProgressRate()
# 
#     def in_work_package(self, uri: str) -> bool:
#         return self.agent.adapt(uri)
# 
#     def set_work_package(self, agent: DataAgent, identities: list or str or None):
#         if isinstance(identities, str):
#             identities = [identities]
#         self.identities = identities
#         self.agent = agent
# 
#     def run(self):
#         print('Update task start.')
# 
#         self.__patch_count = 0
#         self.__apply_count = 0
#         try:
#             # Catch "pymongo.errors.ServerSelectionTimeoutError: No servers found yet" exception and continue.
#             self.__execute_update()
#         except Exception as e:
#             print('Update got Exception: ')
#             print(e)
#             print(traceback.format_exc())
#             print('Continue...')
#         finally:
#             if self.__future is not None:
#                 self.__future.cancel()
#         print('Update task finished.')
# 
#     def quit(self):
#         self.__quit = True
# 
#     def identity(self) -> str:
#         return self.agent.base_uri() if self.agent is not None else ''
# 
#     # ------------------------------------- Task -------------------------------------
# 
#     def __execute_update(self):
#         # Get identities here to ensure we can get the new list after stock info updated
#         update_list = self.identities if self.identities is not None and len(self.identities) > 0 else \
#                       self.agent.update_list()
#         if update_list is None or len(update_list) == 0:
#             update_list = [None]
#         progress = len(update_list)
# 
#         self.clock.reset()
#         self.progress.reset()
#         self.progress.set_progress(self.agent.base_uri(), 0, progress)
# 
#         for identity in update_list:
#             while (self.__patch_count - self.__apply_count > 20) and not self.__quit:
#                 time.sleep(0.5)
#                 continue
#             if self.__quit:
#                 break
# 
#             print('------------------------------------------------------------------------------------')
# 
#             if identity is not None:
#                 # Optimise: Update not earlier than listing date.
#                 listing_date = self.__data_hub.get_data_utility().get_securities_listing_date(identity, default_since())
# 
#                 if self.__force:
#                     since, until = listing_date, now()
#                 else:
#                     since, until = self.__data_center.calc_update_range(self.agent.base_uri(), identity)
#                     since = max(listing_date, since)
#                 time_serial = (since, until)
#             else:
#                 time_serial = None
# 
#             patch = self.__data_center.build_local_data_patch(
#                 self.agent.base_uri(), identity, time_serial, force=self.__force)
#             self.__patch_count += 1
#             print('Patch count: ' + str(self.__patch_count))
# 
#             self.__future = self.__pool.submit(self.__execute_persistence,
#                                                self.agent.base_uri(), identity, patch)
# 
#         if self.__future is not None:
#             print('Waiting for persistence task finish...')
#             self.__future.result()
#         self.clock.freeze()
#         # self.__ui.task_finish_signal[UpdateTask].emit(self)
# 
#     def __execute_persistence(self, uri: str, identity: str, patch: tuple) -> bool:
#         try:
#             if patch is not None:
#                 self.__data_center.apply_local_data_patch(patch)
#             if identity is not None:
#                 self.progress.set_progress([uri, identity], 1, 1)
#             self.progress.increase_progress(uri)
#         except Exception as e:
#             print('Persistence error: ' + str(e))
#             print(traceback.format_exc())
#             return False
#         finally:
#             self.__apply_count += 1
#             print('Persistence count: ' + str(self.__apply_count))
#         return True


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


# ------------------------------- Update Resouce Task -------------------------------

# class UpdateResTask(TaskQueue.Task):
#     def __init__(self, ui):
#         super(UpdateResTask, self).__init__('UpdateResTask')
#         self.__ui = ui
#
#     def run(self):
#         self.__ui.update_task_progress()
#
#     def identity(self) -> str:
#         return 'UpdateResTask'


# # ------------------------------ UpdateStockListTask ------------------------------
#
# class UpdateStockListTask(TaskQueue.Task):
#     def __init__(self, data_utility):
#         super(UpdateStockListTask, self).__init__('UpdateStockListTask')
#         self.__data_utility = data_utility
#
#     def run(self):
#         print('Update stock list task start.')
#         self.__data_utility.refresh_cache()
#         print('Update stock list task finished.')
#
#     def identity(self) -> str:
#         return 'UpdateStockListTask'


# ---------------------------------------------------- DataUpdateUi ----------------------------------------------------

class DataUpdateUi(QWidget):
    # task_finish_signal = pyqtSignal()
    refresh_finish_signal = pyqtSignal()

    INDEX_CHECK = 0
    INDEX_ITEM = 1
    INDEX_STATUS = 8
    TABLE_HEADER = ['', 'Item', 'Local Data Since', 'Local Data Until', 'Latest Update',
                    'Update Estimation', 'Sub Update', 'Update', 'Status']

    def get_uri_sub_update(self, uri: str) -> list or None:
        return self.__context.get_sas_interface().sas_get_data_agent_update_list(uri)
        # agent = self.__data_hub.get_data_center().get_data_agent(uri)
        # if agent is not None:
        #     return agent.update_list()
        # else:
        #     print('Error: Agent of URI %s is None.' % uri)

    def __init__(self, context: UiContext):
        super(DataUpdateUi, self).__init__()

        self.__context = context
        # self.__res_sync = ResourceSync(context.get_sas_interface())

        # Table content
        self.__display_uri = []
        self.__data_agent_prob = {}
        self.__display_identities = None
        self.__display_table_lines = []

        # Page related
        self.__page = 0
        self.__item_per_page = 20

        # Mark if it's first update. If yes, the update complete alarm will not be showed
        self.__first_post_update = True
        # Mark if we just posted the update task, if yes, it will keeping update until we get not empty update res ids
        self.__just_post_update = False
        # Post update per 10 seconds
        self.__post_update_timeout = 10

        # # For processing updating
        # self.__processing_update_tasks = []
        # # Fot task counting
        # self.__processing_update_tasks_count = []

        # self.__task_res_id = []
        # self.__task_progress = {}
        # self.__total_progress = ProgressRate()

        self.__current_update_task: ResourceUpdateTask = None

        # self.task_finish_signal.connect(self.__on_task_done)
        self.refresh_finish_signal.connect(self.update_table_display)

        # Timer for update status
        self.__timer = QTimer()
        self.__timer.setInterval(1000)
        self.__timer.timeout.connect(self.on_timer)
        self.__timer.start()

        self.__lock = threading.Lock()

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

        # # Post update and cache stock list after posting RefreshTask
        # data_utility = self.__data_hub.get_data_utility()
        # self.__context.get_task_queue().add_observer(self)
        # self.__context.get_task_queue().append_task(UpdateStockListTask(data_utility))

        # self.__context.get_task_queue().add_observer(self)
        self.__context.get_task_queue().append_task(RefreshTask(self))

        self.post_progress_updater()

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
        self.__context.get_sas_interface().sas_execute_update(uri, identity, None, False)
        self.post_progress_updater()
        # self.__task_res_id.append(res_id)
        # self.__context.get_res_sync().add_sync_resource(res_id, 'progress')

    def on_force_update_button(self, uri: str, identity: str):
        print('Force update ' + uri + ' : ' + str(identity))
        self.__context.get_sas_interface().sas_execute_update(uri, identity, None, True)
        self.post_progress_updater()
        # self.__task_res_id.append(res_id)
        # self.__context.get_res_sync().add_sync_resource(res_id, 'progress')

    def on_batch_update(self, force: bool):
        update_uris = []
        for i in range(self.__table_main.RowCount()):
            if self.__table_main.GetItemCheckState(i, DataUpdateUi.INDEX_CHECK) == Qt.Checked:
                item_id = self.__table_main.GetItemText(i, DataUpdateUi.INDEX_ITEM)
                # A little ugly...To distinguish it's uri or securities identity
                if self.__display_identities is None:
                    # For sort
                    update_uris.append(item_id)
                    # self.__context.get_sas_interface().sas_execute_update(item_id, None, force)
                    # self.__task_res_id.append(res_id)
                else:
                    self.__context.get_sas_interface().sas_execute_update(self.__display_uri[0], item_id, None, force)
                    # self.__task_res_id.append(res_id)

        # Sort by update priority
        sorted(update_uris, key=lambda x: self.__data_agent_prob[x]['update_priority'], reverse=True)
        # Only if the update_uris has contents.
        for uri in update_uris:
            self.__context.get_sas_interface().sas_execute_update(uri, None, None, force)

        self.post_progress_updater()

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
        if self.__current_update_task is None:
            if self.__post_update_timeout > 0:
                self.__post_update_timeout -= 1
            else:
                # Check per 10s to avoid any update missing
                self.post_progress_updater()
                self.__post_update_timeout = 10
            return

        if self.__current_update_task.working():
            # Waiting for update
            return

        total_progress = ProgressRate()
        updater: ResourceTagUpdater = self.__current_update_task.get_updater()
        updated_res_id = updater.get_resource_ids()

        if updated_res_id is None:
            # The server might be killed
            return

        done_progress = []
        for res_id in updated_res_id:
            progress: ProgressRate = updater.get_resource(res_id, 'progress')
            if progress is None:
                continue
            total_progress.combine_with(progress)
            if progress.progress_done():
                done_progress.append(res_id)

        for i in range(self.__table_main.RowCount()):
            item_id = self.__table_main.GetItemText(i, DataUpdateUi.INDEX_ITEM)
            # A little ugly...To distinguish it's uri or securities identity
            if self.__display_identities is None:
                uri = item_id
                prog_id = uri
            else:
                uri = self.__display_uri[0]
                prog_id = [uri, item_id]

            if not total_progress.has_progress(prog_id):
                text = ['']
            else:
                rate = total_progress.get_progress_rate(prog_id)
                if rate < 0.0001:
                    text = ['Waiting...']
                else:
                    text = ['%.2f%%' % (rate * 100)]

            # for res_id, progress in self.__task_progress.items():
            #     if not task.in_work_package(uri):
            #         continue
            #     text = []
            #     if task.status() in [TaskQueue.Task.STATUS_IDLE, TaskQueue.Task.STATUS_PENDING]:
            #         text.append('等待中...')
            #     else:
            #         if progress.has_progress(prog_id):
            #             rate = progress.get_progress_rate(prog_id)
            #             text.append('%ss' % task.clock.elapsed_s())
            #             text.append('%.2f%%' % (rate * 100))
            #         if task.status() == TaskQueue.Task.STATUS_CANCELED:
            #             text.append('[Canceled]')
            #         elif task.status() == TaskQueue.Task.STATUS_FINISHED:
            #             text.append('[Finished]')
            #         elif task.status() == TaskQueue.Task.STATUS_EXCEPTION:
            #             text.append('[Error]')

            self.__table_main.SetItemText(i, DataUpdateUi.INDEX_STATUS, ' | '.join(text))

        if len(updated_res_id) > 0:
            if len(done_progress) != len(updated_res_id):
                # Progress not done yet, post update
                self.post_progress_updater()
            else:
                # Progress done, not post update
                self.__context.get_sas_interface().sas_delete_resource(done_progress)
                self.__current_update_task = None
                # If progress done at process startup, do not pop up message box
                if not self.__first_post_update:
                    self.__on_update_done()
        # --------- Just for the progress performs good ---------
                self.__first_post_update = False
                self.__just_post_update = False
        elif self.__just_post_update:
            # If just post update, it may not get the progress at the first time, retry.
            self.post_progress_updater()
            self.__just_post_update = False
        else:
            self.__current_update_task = None
        self.__post_update_timeout = 10

        # if not total_progress.progress_done():
        #     self.__context.get_task_queue().append_task(UpdateResTask(self))

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
        self.__context.get_task_queue().append_task(task)

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
                update_list = self.__context.get_sas_interface().sas_get_data_agent_update_list(uri)
                if update_list is not None and len(update_list) > 0:
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

    # -------------------- Call by update RefreshTask --------------------

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

        update_tags = uri.split('.') + ([identity] if identity is not None else [])
        since, until = self.__context.get_sas_interface().sas_get_local_data_range_from_update_table(update_tags)
        
        if since is None or until is None:
            # Query from DB, very slow. In theory we can get updated range from update table.
            since, until = self.__context.get_sas_interface().sas_get_data_range(uri, identity)
        if until is not None:
            update_since = min(tomorrow_of(until), now())
            update_until = now()
        else:
            pass
            update_since, update_until = self.__context.get_sas_interface().sas_calc_update_range(uri, identity)

        update_tags = uri.split('.')
        latest_update = self.__context.get_sas_interface().sas_get_last_update_time_from_update_table(update_tags)

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

    # -------------------------------------------------------------------------

    # def update_task_progress(self):
    #     self.lock()
    #     task_res_id = self.__task_res_id.copy()
    #     self.unlock()
    #
    #     task_progress = {}
    #     total_progress = ProgressRate()
    #     for res_id in task_res_id:
    #         progress = self.__context.get_res_sync().get_resource(res_id, 'progress')
    #         task_progress[res_id] = progress
    #         total_progress.combine_with(progress)
    #
    #     self.lock()
    #     self.__task_progress = task_progress
    #     self.__total_progress = total_progress
    #     self.unlock()
    #
    # def clear_finished_progress(self):
    #     self.lock()
    #     for res_id, progress in self.__task_progress.items():
    #         if progress.progress_done():
    #             if res_id in self.__task_res_id:
    #                 self.__task_res_id.remove(res_id)
    #     self.unlock()
    #
    # # -------------------- Call by update UpdateResTask --------------------

    # --------------------------------------------------------------------------

    def __to_top_level(self):
        # Temporary exclude Factor related data

        probs = self.__context.get_sas_interface().sas_get_data_agent_probs()
        self.__data_agent_prob = {prob['uri']: prob for prob in probs}

        support_uri = self.__context.get_sas_interface().sas_get_all_uri()
        self.__display_uri = [uri for uri in support_uri if self.__data_agent_prob[uri]['update_priority'] > 0]

        self.__display_identities = None
        self.__page = 0
        self.update_table()

    def __to_detail_level(self, uri: str):
        self.__display_uri = [uri]
        self.__display_identities = self.get_uri_sub_update(uri)
        self.__page = 0
        self.update_table()

    # def __build_post_update_task(self, uri: str, identities: list or None, force: bool) -> bool:
    #     agent = self.__data_center.get_data_agent(uri)
    #     task = UpdateTask(self, self.__data_hub, self.__data_center, force)
    #     task.set_work_package(agent, identities)
    #     self.__processing_update_tasks.append(task)
    #     self.__processing_update_tasks_count.append(task)
    #     ret = self.__context.get_task_queue().append_task(task)
    #     # After updating market info, also update stock list cache
    #     if ret and (uri == 'Market.SecuritiesInfo' or uri == 'Market.IndexInfo'):
    #         data_utility = self.__data_hub.get_data_utility()
    #         self.__context.get_task_queue().append_task(UpdateStockListTask(data_utility))
    #     return ret

    # ---------------------------------------------------------------------------------

    # def on_task_updated(self, task, change: str):
    #     if change in ['canceled', 'finished']:
    #         pass
    #         # if task in self.__processing_update_tasks_count:
    #         #     self.task_finish_signal[UpdateTask].emit(task)

    # def __on_task_done(self):
    #     pass
        # if task in self.__processing_update_tasks_count:
        #     self.__processing_update_tasks_count.remove(task)
        #     print('Finish task: %s, remaining count: %s' % (task.name(), len(self.__processing_update_tasks_count)))
        #     if len(self.__processing_update_tasks_count) == 0:
        #         QMessageBox.information(self,
        #                                 QtCore.QCoreApplication.translate('main', '更新完成'),
        #                                 QtCore.QCoreApplication.translate('main', '数据更新完成'),
        #                                 QMessageBox.Ok, QMessageBox.Ok)
        #         self.__processing_update_tasks.clear()
        #         self.update_table()
        # else:
        #     print('Impossible: Cannot find finished task in task list.')

    def lock(self):
        self.__lock.acquire()

    def unlock(self):
        self.__lock.release()

    def post_progress_updater(self):
        updater = ResourceTagUpdater(self.__context.get_sas_interface(), 'Data Update Progress Updater')
        updater.set_resource_tags('update_task')
        updater.set_update_resource_keys('progress')

        update_task = ResourceUpdateTask(updater)
        self.__context.get_task_queue().append_task(update_task)
        self.__current_update_task = update_task
        self.__post_update_timeout = 10
        self.__just_post_update = True

    def __on_update_done(self):
        QMessageBox.information(self,
                                QtCore.QCoreApplication.translate('main', '更新完成'),
                                QtCore.QCoreApplication.translate('main', '数据更新完成'),
                                QMessageBox.Ok, QMessageBox.Ok)
        self.update_table()


# ----------------------------------------------------------------------------------------------------------------------

def main():
    from StockAnalysisSystem.interface.interface_local import LocalInterface

    project_path = os.path.dirname(os.path.dirname(os.getcwd()))

    local_if = LocalInterface()
    local_if.if_init(project_path=project_path)

    context = UiContext()
    context.set_sas_interface(local_if)

    app = QApplication(sys.argv)
    dlg = WrapperQDialog(DataUpdateUi(context))
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

