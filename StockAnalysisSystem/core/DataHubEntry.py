from .Utiltity.common import *
from .DataHub.DataAgentBuilder import *
from .Utiltity.task_queue import TaskQueue
from .DataHub.DataUtility import DataUtility
from .Database.DatabaseEntry import DatabaseEntry
from .Utiltity.plugin_manager import PluginManager
from .DataHub.UniversalDataCenter import UniversalDataCenter

from concurrent.futures import ThreadPoolExecutor, Future, ProcessPoolExecutor, Executor


class UpdateHelper:
    class UpdateTask(TaskQueue.Task):
        def __init__(self, data_center: UniversalDataCenter, data_utility: DataUtility,
                     uri: str, update_items: [str] or None = None, force: bool = False,
                     progress: ProgressRate or None = None, clock: Clock or None = None, **kwargs):
            super(UpdateHelper.UpdateTask, self).__init__('UpdateHelper.UpdateTask')
            self.__uri = uri
            self.__force = force
            self.__clock = clock
            self.__progress = progress

            if str_available(update_items):
                self.__update_items = [update_items]
            elif isinstance(update_items, (list, tuple, set)):
                self.__update_items = list(update_items)
            else:
                self.__update_items = None
            self.__extra = kwargs

            # Thread pool
            self.__quit = False
            self.__patch_count = 0
            self.__apply_count = 0
            self.__last_future = None
            self.__pool = ThreadPoolExecutor(max_workers=1)

            self.__data_center = data_center
            self.__data_utility = data_utility
            self.__uri_data_agent = self.__data_center.get_data_agent(self.__uri)

        # ------------------------------------ Interface of TaskQueue.Task ------------------------------------

        def run(self):
            print('Update task start.')
            try:
                # Catch "pymongo.errors.ServerSelectionTimeoutError: No servers found yet" exception and continue.
                self.__execute_update()
            except Exception as e:
                print('Update got Exception: ')
                print(e)
                print(traceback.format_exc())
                print('Continue...')
            finally:
                if self.__last_future is not None:
                    self.__last_future.cancel()
                    self.__last_future = None
            print('Update task finished.')

        def quit(self):
            self.__quit = True

        def identity(self) -> str:
            return self.__uri_data_agent.base_uri() if self.__uri_data_agent is not None else ''

        # ------------------------------------- Task -------------------------------------

        def __execute_update(self):
            # Get identities here to ensure we can get the new list after stock info updated
            update_list = self.__update_items if self.__update_items is not None and len(self.__update_items) > 0 else \
                self.__uri_data_agent.update_list()
            if update_list is None or len(update_list) == 0:
                update_list = [None]
            progress = len(update_list)

            if self.__clock is not None:
                self.__clock.reset()
            if self.__progress is not None:
                self.__progress.reset()
                self.__progress.set_progress(self.__uri, 0, progress)

            self.__patch_count = 0
            self.__apply_count = 0
            for identity in update_list:
                while (self.__patch_count - self.__apply_count > 20) and not self.__quit:
                    time.sleep(0.5)
                    continue
                if self.__quit:
                    break

                print('------------------------------------------------------------------------------------')

                patch = self.__execute_fetching(identity)
                self.__patch_count += 1
                print('Patch count: ' + str(self.__patch_count))
                self.__last_future = self.__pool.submit(self.__execute_persistence, identity, patch)

            if self.__last_future is not None:
                print('Waiting for persistence task finish...')
                self.__last_future.result()
            if self.__clock is not None:
                self.__clock.freeze()

        def __execute_fetching(self, identity: str or None):
            if self.__quit:
                return None
            if identity is not None:
                # Optimise: Update not earlier than listing date.
                listing_date = self.__data_utility.get_securities_listing_date(identity, default_since())

                if self.__force:
                    since, until = listing_date, now()
                else:
                    since, until = self.__data_center.calc_update_range(self.__uri_data_agent.base_uri(), identity)
                    since = max(listing_date, since)
                time_serial = (since, until)
            else:
                time_serial = None

            patch = self.__data_center.build_local_data_patch(
                self.__uri_data_agent.base_uri(), identity, time_serial, force=self.__force)
            return patch

        def __execute_persistence(self, identity: str, patch: tuple) -> bool:
            if self.__quit or patch is None:
                return False
            try:
                if patch is not None:
                    self.__data_center.apply_local_data_patch(patch)
                uri = self.__uri_data_agent.base_uri()
                if identity is not None:
                    self.__progress.set_progress([uri, identity], 1, 1)
                self.__progress.increase_progress(uri)
            except Exception as e:
                print(e)
                return False
            finally:
                self.__apply_count += 1
                print('Persistence count: ' + str(self.__apply_count))
            return True

    UPDATE_ITEM_NONE = 0
    UPDATE_ITEM_AUTO = 1

    UPDATE_RANGE_NONE = 0
    UPDATE_RANGE_AUTO = 1
    UPDATE_RANGE_FORCE = 2

    PERSISTENCE_NO = 0
    PERSISTENCE_SYNC = 1
    PERSISTENCE_THREAD = 2
    PERSISTENCE_PROCESS = 3

    def __init__(self, data_utility, update_task_queue: TaskQueue):
        self.__data_center = data_utility.get_data_center()
        self.__data_utility = data_utility.__data_utility()
        self.__update_task_queue = update_task_queue if update_task_queue is not None else TaskQueue()

        self.__pool = ThreadPoolExecutor(max_workers=1)
        self.__pending_task = []

    def smart_update(self, uri: str,
                     update_items: str or [str] or int = UPDATE_ITEM_NONE,
                     update_range: (datetime.datetime, datetime.datetime) or int = UPDATE_RANGE_AUTO,
                     **kwargs) -> bool:
        pass

    def block_update(self, uri: str, update_items: str or [str],
                     update_range: (datetime.datetime, datetime.datetime), **kwargs) -> bool:
        if update_items is None:
            return False
        if not isinstance(update_range, (tuple, list, set)) or \
                len(update_range) != 2 or \
                not isinstance(update_range[0], datetime.datetime) or \
                not isinstance(update_range[1], datetime.datetime):
            # Must specify update range
            return False
        return self.__update_entry(uri, update_items, update_range, **kwargs)

    def slice_update(self, uri: str, update_items: str or [str] or None,
                     update_time: datetime.datetime, **kwargs):
        if not isinstance(update_time, datetime.datetime):
            return False
        return self.__update_entry(uri, update_items, update_time, **kwargs)

    def serial_update(self, uri: str, update_items: str or [str],
                      update_range: (datetime.datetime, datetime.datetime) or int = UPDATE_RANGE_AUTO, **kwargs):
        return self.__update_entry(uri, update_items, update_range, **kwargs)

    # ---------------------------------------------------------------------------------------------

    PATCH_COUNT_INDEX = 0
    APPLY_COUNT_INDEX = 1

    def __update_entry(self, uri: str, update_items: str or [str] or int = UPDATE_ITEM_AUTO,
                       update_range: (datetime.datetime, datetime.datetime) or int = UPDATE_RANGE_AUTO, **kwargs):
        clock = kwargs.get('clock', None)
        progress = kwargs.get('progress', None)
        quit_flag = kwargs.get('quit_flag', [False])

        # ---------------------- Calculate Update Items ----------------------

        if update_items == UpdateHelper.UPDATE_ITEM_NONE:
            update_list = [None]
        elif update_items == UpdateHelper.UPDATE_ITEM_AUTO:
            data_agent = self.__data_center.get_data_agent(uri)
            update_list = data_agent.update_list()
        elif str_available(update_items):
            update_list = [update_items]
        elif isinstance(update_items, (list, tuple, set)):
            update_list = list(update_items)
        else:
            update_list = [None]

        if len(update_list) == 0:
            update_list = [None]

        if clock is not None:
            clock.reset()
        if progress is not None:
            progress.reset()
            progress(uri, 0, len(update_list))

        counter = [0, 0]
        last_future = None

        for identity in update_list:
            if quit_flag[0]:
                break
            while counter[UpdateHelper.PATCH_COUNT_INDEX] - counter[UpdateHelper.APPLY_COUNT_INDEX] > 20:
                time.sleep(0.5)
                continue

            # ------------------- Calculate Update Time Serial -------------------

            if update_range == UpdateHelper.UPDATE_RANGE_NONE:
                time_serial = None
            elif update_range == UpdateHelper.UPDATE_RANGE_AUTO:
                time_serial = self.__data_utility.calc_update_range(uri, identity, None)
            elif update_range == UpdateHelper.UPDATE_RANGE_FORCE:
                listing_date = self.__data_utility.get_securities_listing_date(identity, default_since())
                time_serial = listing_date, now()
            else:
                time_serial = self.__data_utility.calc_update_range(uri, identity, update_range)

            # -------------------------- Execute Update --------------------------

            patch = self.__data_center.build_local_data_patch(uri, identity, time_serial,
                                                              force=update_range == UpdateHelper.UPDATE_RANGE_FORCE)
            counter[UpdateHelper.PATCH_COUNT_INDEX] += 1
            print('Patch count: ' + str(counter[UpdateHelper.PATCH_COUNT_INDEX]))

            # ----------------------- Execute Persistence ------------------------

            last_future = self.__persistence_entry(uri, identity, patch, counter, **kwargs)

        if isinstance(last_future, Future):
            print('Waiting for persistence task finish...')
            last_future.result()
        elif not last_future:
            print('Persistence fail.')
        if clock is not None:
            clock.freeze()

        return True

    def __persistence_entry(self, uri: str, identity: str,
                            patch: tuple, counter: [int, int], **kwargs) ->Future or bool:
        persistence = kwargs.get('persistence', UpdateHelper.PERSISTENCE_THREAD)

        if persistence == UpdateHelper.PERSISTENCE_NO:
            return True
        elif persistence == UpdateHelper.PERSISTENCE_SYNC:
            return self.__execute_persistence(uri, identity, patch, counter, **kwargs)
        elif persistence == UpdateHelper.PERSISTENCE_THREAD:
            return self.__pool.submit(self.__execute_persistence, uri, identity, patch, counter, **kwargs)
        else:
            return False

    def __execute_persistence(self, uri: str, identity: str, patch: tuple, counter: [int, int], **kwargs) -> bool:
        progress = kwargs.get('progress', None)
        quit_flag = kwargs.get('quit_flag', [False])

        if quit_flag[0] or patch is None:
            return False
        try:
            if patch is not None:
                self.__data_center.apply_local_data_patch(patch)
            if progress is not None:
                if identity is not None:
                    progress.set_progress([uri, identity], 1, 1)
                progress.increase_progress(uri)
        except Exception as e:
            print(e)
            return False
        finally:
            counter[UpdateHelper.APPLY_COUNT_INDEX] += 1
            print('Persistence count: ' + str(counter[UpdateHelper.APPLY_COUNT_INDEX]))
        return True


class DataHubEntry:
    def __init__(self, database_entry: DatabaseEntry, collector_plugin: PluginManager):
        self.__database_entry = database_entry
        self.__collector_plugin = collector_plugin

        self.__data_extra = {}
        self.__data_center = UniversalDataCenter(database_entry, collector_plugin)
        self.__data_utility = DataUtility(self.__data_center)

        self.__data_agents = []
        self.build_data_agent()

    def reg_data_extra(self, name: str, ext: any):
        if name in self.__data_extra:
            print('Warning: Data extra %s exists - ignore.' % name)
            return
        self.__data_extra[name] = ext

    def get_data_extra(self, name: str) -> any:
        return self.__data_extra.get(name, None)

    def get_data_center(self) -> UniversalDataCenter:
        return self.__data_center

    def get_data_utility(self) -> DataUtility:
        return self.__data_utility

    # ------------------------------------------------------------------------------------------------------------------

    def build_data_agent(self):
        self.__data_agents = build_data_agent(self.__database_entry)
        for agent in self.__data_agents:
            self.get_data_center().register_data_agent(agent)
















