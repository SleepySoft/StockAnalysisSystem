from StockAnalysisSystem.code.AnalyzerEntry import StrategyEntry, AnalysisResult
from StockAnalysisSystem.core.Utiltity.task_future import *
from StockAnalysisSystem.core.DataHubEntry import DataHubEntry


# For core.interface, without ui.

class SasAnalysisTask(TaskFuture):
    def __init__(self, strategy_entry: StrategyEntry, data_hub: DataHubEntry,
                 securities: str or [str], analyzer_list: [str], time_serial: tuple, enable_from_cache: bool):
        super(SasAnalysisTask, self).__init__('SasAnalysisTask')
        self.__data_hub = data_hub
        self.__strategy = strategy_entry
        self.__securities = securities
        self.__analyzer_list = analyzer_list
        self.__time_serial = time_serial
        self.__enable_from_cache = enable_from_cache

    def run(self):
        stock_list = self.select()
        result_list = self.analysis(stock_list)
        self.update_result(result_list)

    def identity(self) -> str:
        return 'SasAnalysisTask'

    # -----------------------------------------------------------------------------

    def select(self) -> [str]:
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

    def analysis(self, securities_list: [str]) -> [AnalysisResult]:
        total_result = self.__strategy.analysis_advance(
            securities_list, self.__analyzer_list, self.__time_serial,
            self.get_progress_rage(), enable_from_cache=self.__enable_from_cache)
        return total_result


