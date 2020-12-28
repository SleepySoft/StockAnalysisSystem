from .DataHub.DataAgent import *
from .Utiltity.resource_task import *
from .Utiltity.time_utility import *
from .DataHubEntry import DataHubEntry
from .AnalyzerEntry import StrategyEntry, AnalysisResult
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Executor


class SasUpdateTask(ResourceTask):
    def __init__(self, data_hub, data_center, force: bool):
        super(SasUpdateTask, self).__init__('UpdateTask')
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
            self.update_result(True)
        except Exception as e:
            self.update_result(False)
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
            print('Persistence error: ' + str(e))
            print(traceback.format_exc())
            return False
        finally:
            self.__apply_count += 1
            print('Persistence count: ' + str(self.__apply_count))
        return True


class SasAnalysisTask(ResourceTask):
    def __init__(self, strategy_entry: StrategyEntry, data_hub: DataHubEntry,
                 securities: str or [str], analyzer_list: [str], time_serial: tuple,
                 enable_from_cache: bool, **kwargs):
        super(SasAnalysisTask, self).__init__('SasAnalysisTask')
        self.__data_hub = data_hub
        self.__strategy = strategy_entry
        self.__securities = securities
        self.__analyzer_list = analyzer_list
        self.__time_serial = time_serial
        self.__enable_from_cache = enable_from_cache
        self.__extra_params = kwargs

    def run(self):
        stock_list = self.selected_securities()
        result_list = self.analysis(stock_list)
        self.update_result(result_list)

    def identity(self) -> str:
        return 'SasAnalysisTask'

    # -----------------------------------------------------------------------------

    def analysis(self, securities_list: [str]) -> [AnalysisResult]:
        total_result = self.__strategy.analysis_advance(
            securities_list, self.__analyzer_list, self.__time_serial, self.get_progress_rate(),
            enable_from_cache=self.__enable_from_cache,
            enable_update_cache=self.__extra_params.get('enable_update_cache', True),
            debug_load_json=self.__extra_params.get('debug_load_json', False),
            debug_dump_json=self.__extra_params.get('debug_dump_json', False),
            dump_path=self.__extra_params.get('dump_path', ''),
        )
        return total_result

    def selected_securities(self) -> [str]:
        if self.__securities is None:
            data_utility = self.__data_hub.get_data_utility()
            stock_list = data_utility.get_stock_identities()
        elif isinstance(self.__securities, str):
            stock_list = [self.__securities]
        elif isinstance(self.__securities, (list, tuple, set)):
            stock_list = list(self.__securities)
        else:
            stock_list = []
        return stock_list


