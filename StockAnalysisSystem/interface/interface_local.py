import uuid
import datetime
from functools import partial

import pandas as pd

from .interface import SasInterface as sasIF
import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.core.Utility.common import *
from StockAnalysisSystem.core.DataHub.DataAgent import *
from StockAnalysisSystem.core.Utility.resource_task import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.AnalyzerEntry import StrategyEntry
from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem
from StockAnalysisSystem.core.Utility.resource_manager import ResourceManager
from StockAnalysisSystem.core.DataHub.UniversalDataCenter import UniversalDataCenter

from StockAnalysisSystem.core.DataHub.DataAgent import *
from StockAnalysisSystem.core.Utility.resource_task import *
from StockAnalysisSystem.core.Utility.time_utility import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry
from StockAnalysisSystem.core.AnalyzerEntry import StrategyEntry, AnalysisResult
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Executor


class SasUpdateTask(ResourceTask):
    def __init__(self, data_hub, data_center, resource_manager: ResourceManager, force: bool):
        super(SasUpdateTask, self).__init__('UpdateTask', resource_manager)
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
        self.__agent = None
        self.__clock = Clock()
        self.__identities = []

        # Add resource tags here
        resource_manager.set_resource_tags(self.res_id(), ['update_task'])

    def in_work_package(self, uri: str) -> bool:
        return self.__agent.adapt(uri)

    def set_work_package(self, agent: DataAgent, identities: list or str or None):
        if isinstance(identities, str):
            identities = [identities]
        self.__identities = identities
        self.__agent = agent

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
        return self.__agent.base_uri() if self.__agent is not None else ''

    # ------------------------------------- Task -------------------------------------

    def __execute_update(self):
        # Get identities here to ensure we can get the new list after stock info updated
        update_list = self.__identities if self.__identities is not None and len(self.__identities) > 0 else \
                      self.__agent.update_list()
        if update_list is None or len(update_list) == 0:
            update_list = [None]
        progress = len(update_list)

        self.__clock.reset()
        self.progress().reset()
        self.progress().set_progress(self.__agent.base_uri(), 0, progress)

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
                    since, until = self.__data_center.calc_update_range(self.__agent.base_uri(), identity)
                    since = max(listing_date, since)
                time_serial = (since, until)
            else:
                time_serial = None

            patch = self.__data_center.build_local_data_patch(
                self.__agent.base_uri(), identity, time_serial, force=self.__force)
            self.__patch_count += 1
            print('Patch count: ' + str(self.__patch_count))

            self.__future = self.__pool.submit(self.__execute_persistence,
                                               self.__agent.base_uri(), identity, patch)

        if self.__future is not None:
            print('Waiting for persistence task finish...')
            self.__future.result()
        self.__clock.freeze()
        # self.__ui.task_finish_signal[UpdateTask].emit(self)

    def __execute_persistence(self, uri: str, identity: str, patch: tuple) -> bool:
        try:
            if patch is not None:
                self.__data_center.apply_local_data_patch(patch)
            if identity is not None:
                self.progress().set_progress([uri, identity], 1, 1)
            self.progress().increase_progress(uri)
        except Exception as e:
            print('Persistence error: ' + str(e))
            print(traceback.format_exc())
            return False
        finally:
            self.__apply_count += 1
            print('Persistence count: ' + str(self.__apply_count))
        return True


class SasAnalysisTask(ResourceTask):
    def __init__(self, strategy_entry: StrategyEntry, data_hub: DataHubEntry, resource_manager: ResourceManager,
                 securities: str or [str], analyzer_list: [str], time_serial: tuple, enable_from_cache: bool, **kwargs):
        super(SasAnalysisTask, self).__init__('SasAnalysisTask', resource_manager)
        self.__data_hub = data_hub
        self.__strategy = strategy_entry
        self.__securities = securities
        self.__analyzer_list = analyzer_list
        self.__time_serial = time_serial
        self.__enable_from_cache = enable_from_cache
        self.__extra_params = kwargs

        # Add resource tags here
        resource_manager.set_resource_tags(self.res_id(), ['analysis_task'])

    def run(self):
        stock_list = self.selected_securities()
        result_list = self.analysis(stock_list)
        self.update_result(result_list)

    def identity(self) -> str:
        return 'SasAnalysisTask'

    # -----------------------------------------------------------------------------

    def analysis(self, securities_list: [str]) -> [AnalysisResult]:
        total_result = self.__strategy.analysis_advance(
            securities_list, self.__analyzer_list, self.__time_serial, self.progress(),
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


class LocalInterface(sasIF):
    def __init__(self):
        super(LocalInterface, self).__init__()
        self.__resource_manager = ResourceManager()

    # ------------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------- Interface of sasIF -----------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------

    def if_init(self, project_path: str = None, config=None, not_load_config: bool = False) -> bool:
        return sasApi.init(project_path, config, not_load_config)

    # ------------------------------- Resource --------------------------------

    def sas_get_resource(self, res_id: str, key: str or [str]) -> any or [any]:
        list_param = isinstance(key, (list, tuple))
        res_names = key if list_param else [key]
        res = [self.__resource_manager.get_resource(res_id, name) for name in res_names]
        return res if list_param else res[0]

    def sas_find_resource(self,  tags: str or [str]) -> [str]:
        tags = list(tags) if isinstance(tags, (list, tuple, set)) else [str(tags)]
        return self.__resource_manager.find_resource_by_tags(tags)

    def sas_delete_resource(self, res_id: str or [str]) -> bool:
        res_ids = list(res_id) if isinstance(res_id, (list, tuple, set)) else [str(res_id)]
        for _id in res_ids:
            self.__resource_manager.pop_resource(_id)
        return True

    # --------------------------------- Query ---------------------------------

    def sas_query(self, uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> pd.DataFrame or None:
        return sasApi.query(uri, identity, time_serial, **extra)

    # -------------------------------- Datahub --------------------------------

    def sas_execute_update(self, uri: str, identity: str or [str] = None, force: bool = False, **extra) -> str:
        agent = sasApi.data_center().get_data_agent(uri)
        task = SasUpdateTask(sasApi.data_hub(), sasApi.data_center(), self.__resource_manager, force)
        task.set_work_package(agent, identity)
        sasApi.append_task(task)
        return task.res_id()

    def sas_get_all_uri(self) -> [str]:
        probs = sasApi.get_data_agent_info()
        return [prob.get('uri') for prob in probs]

    def sas_get_data_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        return sasApi.get_uri_data_range(uri, identity)

    def sas_calc_update_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        return sasApi.calc_uri_data_update_range(uri, identity)

    def sas_get_data_agent_probs(self) -> [dict]:
        """
        Get list of data agent prob
        :return: List of dict, dict key includes [uri, depot, identity_field, datetime_field]
        """
        probs = sasApi.get_data_agent_info()
        return [{
            'uri': uri,
            'depot': depot,
            'identity_field': identity_field,
            'datetime_field': datetime_field,
        } for uri, depot, identity_field, datetime_field in probs]

    def sas_get_data_agent_update_list(self, uri: str) -> [str]:
        agent: DataAgent = sasApi.data_center().get_data_agent(uri)
        return agent.update_list()

    # ----------------------------- Update Table -----------------------------

    def sas_get_local_data_range_from_update_table(self, update_tags: [str]) -> (datetime.datetime, datetime.datetime):
        return sasApi.get_local_data_range_from_update_table(update_tags)

    def sas_get_last_update_time_from_update_table(self, update_tags: [str]) -> datetime.datetime:
        return sasApi.get_last_update_time_from_update_table(update_tags)

    # -------------------------------- Analyzer --------------------------------

    def sas_execute_analysis(self, securities: str or [str], analyzers: [str], time_serial: (datetime, datetime),
                             enable_from_cache: bool = True, **kwargs) -> str:
        task = SasAnalysisTask(sasApi.strategy_entry(), sasApi.data_hub(), self.__resource_manager,
                               securities, analyzers, time_serial, enable_from_cache, **kwargs)
        sasApi.append_task(task)
        return task.res_id()

    def sas_get_analyzer_probs(self) -> [str]:
        """
        Get list of analyzer prob
        :return: List of dict, dict key includes [uuid, name, detail]
        """
        analyzer_info = sasApi.get_analyzer_info()
        return [{
            'uuid': method_uuid, 'name': method_name, 'detail': method_detail
        } for method_uuid, method_name, method_detail, _ in analyzer_info]

    # -------------------------------------------------- Data Utility --------------------------------------------------

    def sas_auto_query(self, identity: str or [str], time_serial: tuple, fields: [str],
                       join_on: [str] = None) -> pd.DataFrame or [pd.DataFrame]:
        return sasApi.auto_query(identity, time_serial, fields, join_on)

    def sas_get_stock_info_list(self) -> [str]:
        return sasApi.get_stock_info_list()

    def sas_get_stock_identities(self) -> [str]:
        return sasApi.get_stock_identities()

    def sas_guess_stock_identities(self, text: str) -> [str]:
        return sasApi.guess_stock_identities(text)

    def sas_get_all_industries(self) -> [str]:
        return sasApi.get_all_industries()

    def sas_get_industry_stocks(self, industry: str) -> [str]:
        return sasApi.get_industry_stocks(industry)

# ------------------------------------------------------- Factor -------------------------------------------------------

    def sas_get_all_factors(self):
        return sasApi.get_all_factors()

    def sas_get_factor_depends(self, factor: str) -> [str]:
        return sasApi.get_factor_depends(factor)

    def sas_get_factor_comments(self, factor: str) -> str:
        return sasApi.get_factor_comments(factor)

    def sas_factor_query(self, stock_identity: str, factor_name: str or [str],
                         time_serial: tuple, mapping: dict, **extra) -> pd.DataFrame or None:
        return sasApi.factor_query(stock_identity, factor_name, time_serial, mapping, **extra)

    # ---------------------------------------------------- SysCall -----------------------------------------------------

    def sys_call(self, func_name: str, *args, **kwargs):
        return sasApi.sys_call(func_name, *args, **kwargs)

    def has_sys_call(self, func_name: str) -> bool:
        return sasApi.has_sys_call(func_name)

    def get_sys_call_by_group(self, group_name: str) -> [str]:
        return sasApi.get_sys_call_by_group(group_name)







