from .config import Config
from .DataHub.DataAgentBuilder import *
from .DataHub.DataUtility import DataUtility
from .Database.DatabaseEntry import DatabaseEntry
from .Utility.plugin_manager import PluginManager
from .DataHub.UniversalDataCenter import UniversalDataCenter


class DataHubEntry:
    def __init__(self, database_entry: DatabaseEntry, collector_plugin: PluginManager, config: Config):
        self.__database_entry = database_entry
        self.__collector_plugin = collector_plugin
        self.__config = config

        delay_config = config.get('TS_DELAY', None)
        if delay_config is not None:
            from .Utility.CollectorUtility import set_delay_table
            set_delay_table(delay_config)

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
















