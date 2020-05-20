from .DataHub.DataAgentBuilder import *
from .DataHub.DataUtility import DataUtility
from .Database.DatabaseEntry import DatabaseEntry
from .Utiltity.plugin_manager import PluginManager
from .DataHub.UniversalDataCenter import UniversalDataCenter


class DataHubEntry:
    def __init__(self, database_entry: DatabaseEntry, collector_plugin: PluginManager):
        self.__database_entry = database_entry
        self.__collector_plugin = collector_plugin
        self.__data_center = UniversalDataCenter(database_entry, collector_plugin)
        self.__data_utility = DataUtility(self.__data_center)

        self.__data_agents = []
        self.build_data_agent()

    def get_data_center(self) -> UniversalDataCenter:
        return self.__data_center

    def get_data_utility(self) -> DataUtility:
        return self.__data_utility

    # ------------------------------------------------------------------------------------------------------------------

    def build_data_agent(self):
        self.__data_agents = build_data_agent(self.__database_entry)
        for agent in self.__data_agents:
            self.get_data_center().register_data_agent(agent)
















