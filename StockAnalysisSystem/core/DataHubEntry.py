from .DataHub.DataAgentBuilder import *
from .DataHub.DataUtility import DataUtility
from .Database.DatabaseEntry import DatabaseEntry
from .Utiltity.plugin_manager import PluginManager
from StockAnalysisSystem.core.Utiltity.common import *
from .DataHub.UniversalDataCenter import UniversalDataCenter


class UpdateHelper:
    class UpdateTask:
        def __init__(self, data_center: UniversalDataCenter, data_utility: DataUtility,
                     uri: str, update_items: [str] or None = None, force: bool = False,
                     progress: ProgressRate or None = None, clock: Clock or None = None, **kwargs):
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

            self.__quit = False
            self.__extra = kwargs

            self.__data_center = data_center
            self.__data_utility = data_utility
            self.__uri_data_agent = self.__data_center.get_data_agent(self.__uri)

        def quit(self):
            self.__quit = True

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

            for identity in update_list:
                while (self.__patch_count - self.__apply_count > 20) and not self.__quit:
                    time.sleep(0.5)
                    continue
                if self.__quit:
                    break

                print('------------------------------------------------------------------------------------')

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
                self.__patch_count += 1
                print('Patch count: ' + str(self.__patch_count))

                self.__future = self.__pool.submit(self.__execute_persistence,
                                                   self.__uri_data_agent.base_uri(), identity, patch)

            if self.__future is not None:
                print('Waiting for persistence task finish...')
                self.__future.result()
            if self.__clock is not None:
                self.__clock.freeze()

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

    def __init__(self, data_center: UniversalDataCenter, data_utility: DataUtility):
        self.__data_center = data_center
        self.__data_utility = data_utility

        self.__pending_task = []

    def post_update_task(self, task: UpdateTask, finish_callback: collections.Callable or None):
        self.__pending_task.append(task)


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
















