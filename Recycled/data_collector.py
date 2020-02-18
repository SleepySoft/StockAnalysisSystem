import traceback

import pandas as pd
from Recycled import module_manager


# ===================================== Plug-in Interface =====================================

class ITickFetcher:
    pass


class IBarFetcher:
    pass


class IFinaFetcher:
    # In:
    #   stock_code: str -> Stock code
    #   report_type: list of str -> Utiltity.constant.ANNUAL_REPORT_TYPES
    # Return: map()
    #   Key: str -> Utiltity.constant.ANNUAL_REPORT_TYPES
    #   Value: DataFrame -> Columns: ......; Index: Year/Date; Cell: Currency unit in CNY Yuan
    def FetchStockAnnualFinaData(
            self, stock_code: str, report_type: [str],
            year_from: int, year_to: int, extra_param=None) -> {str: pd.DataFrame}: pass

    # Reserved
    def FetchStockQuarterlyFinaData(self):
        pass


class IMarketFetcher:
    # Return: DataFrame -> Columns may include but not limited to:
    #     company_name|stock_name_a|stock_code_a|stock_name_b|stock_code_b|industry
    #     english_name|reg_address|listing_date_a|listing_date_b
    #     area|provinces|city|web_address
    def FetchStockIntroduction(self, extra_param=None) -> pd.DataFrame: pass

    # Reserved
    # In: stock_code: str -> Stock code
    def FetchStockInformation(self, stock_code: str, extra_param=None) -> pd.DataFrame: pass

    # Reserved
    def FetchIndexIntroduction(self, extra_param=None) -> pd.DataFrame:
        pass
    # Reserved
    def FetchIndexInformation(self, extra_param=None) -> pd.DataFrame:
        pass
    # Reserved
    def FetchIndexComponent(self, index_code: str, extra_param=None) -> pd.DataFrame:
        pass


class IReportFetcher:
    # In:
    #   stock_code: str -> Stock code
    #   report_period: str -> Utiltity.constant.REPORT_PERIOD_TYPES
    #   extension: list of str -> pdf|tsv|......
    #   date_from, date_to: str of date -> pdf|tsv|......
    # Return: pd.DataFrame
    #   Column:
    #       stock: str -> Stock code
    #       date: str of date -> 2010|2010-09|2010-09-08
    #       content: bytes -> File data
    def FetchFinaReport(
            self, stock_code: str, report_period: str, extensions: [str],
            date_from: [str], date_to: [str], extra_param=None) -> pd.DataFrame: pass


# ===================================== DataCollector Module =====================================

class FetchContext:

    # Invoking status
    RST_OK = 0
    RST_NONE = 1
    RST_FAIL = 2
    RST_NOT_ACCEPT = 3
    RST_EXCLUDE = 4
    RST_NO_SUCH_FUNCTION = 5

    # Execute mode
    EXE_CONTINUE = 0
    EXE_SPECIFIED = 1
    EXE_RESTART = 2
    EXE_AGAIN = 3
    EXE_ALL = 4

    class PluginContext:
        def __init__(self):
            self.Plugin = ''
            self.Function = ''
            self.Result = None
            self.Status = FetchContext.RST_NONE

    def __init__(self):
        self.ExecuteMode = FetchContext.EXE_CONTINUE
        self.SpecifiedPlugin = ''
        # { function_name : [InvokingResult] }
        self.__invoking_status_table = {}
        self.__last_invoking_status = None
        self.__plugin_loader = module_manager.ModuleManager()

    def Init(self) -> bool:
        return self.__plugin_loader.LoadModuleFromFolder('Collector')

    # ------------------------- Plugin Specify/Exclude -------------------------

    def SpecifyPlugin(self, plugin_name: str):
        self.SpecifiedPlugin = plugin_name
        self.ExecuteMode = FetchContext.EXE_SPECIFIED

    def ExcludePlugin(self, plugin_name: str):
        ir = self.__get_module_invoking_status()
        ir.Status = FetchContext.RST_EXCLUDE

    # ------------------------- Fetching control -------------------------

    def ReFetch(self):
        self.SpecifiedPlugin = ''
        self.ExecuteMode = FetchContext.EXE_AGAIN

    def FetchAll(self):
        self.SpecifiedPlugin = ''
        self.ExecuteMode = FetchContext.EXE_ALL

    def ContinueFetching(self):
        self.SpecifiedPlugin = ''
        self.ExecuteMode = FetchContext.EXE_CONTINUE

    def StartOverFetching(self):
        self.SpecifiedPlugin = ''
        self.ExecuteMode = FetchContext.EXE_RESTART

    def NotAcceptThisResult(self):
        self.SpecifiedPlugin = ''
        if self.__last_invoking_status is not None:
            self.__last_invoking_status.Result = FetchContext.RST_NOT_ACCEPT
        self.ExecuteMode = FetchContext.FETCHING_CONTINUE = True

    # ------------------------- Record and Get status -------------------------

    def UpdateInvokingResult(self, function_name: str, module_name: str, result: object, state: int = RST_OK):
        ir = self.__get_module_invoking_status(function_name, module_name)
        ir.Status = FetchContext.RST_OK
        ir.Result = result
        ir.Status = state
        self.__last_invoking_status = ir
        self.SpecifiedPlugin = module_name
        if self.ExecuteMode == FetchContext.EXE_AGAIN:
            self.ExecuteMode = FetchContext.EXE_CONTINUE

    def GetInvokingState(self, function_name: str, module_name: str) -> int:
        ir = self.__get_module_invoking_status(function_name, module_name)
        return ir.Status

    def GetLastInvokingResult(self) -> PluginContext:
        return self.__last_invoking_status

    # ------------------------- Get/Create PluginContext -------------------------

    def __get_module_invoking_status(self, function_name: str, module_name: str):
        result_list = self.__invoking_status_table.get(function_name, None)
        if result_list is None:
            result_list = []
            self.__invoking_status_table[function_name] = result_list
        for result in result_list:
            if result.Module == module_name:
                return result
        ir = FetchContext.PluginContext()
        ir.Module = module_name
        ir.Function = function_name
        result_list.append(ir)
        return ir


class DataCollector:
    def __init__(self):
        self.__collector_loader = module_manager.ModuleManager()

    def Init(self) -> bool:
        return self.__collector_loader.LoadModuleFromFolder('Collector')

    # --------------------------------------- User Interface ---------------------------------------

    def FetchStockAnnualFinaData(
            self, context: FetchContext, stock_code: str, report_type: [str],
            year_from: int, year_to: int, extra_param=None) -> {str: pd.DataFrame}:
        return self.__safe_dynamic_run(context, 'FetchStockAnnualFinaData',
                                       stock_code, report_type, year_from, year_to, extra_param)

    def FetchStockIntroduction(self, context: FetchContext, extra_param=None) -> pd.DataFrame:
        return self.__safe_dynamic_run(context, 'FetchStockIntroduction', extra_param)

    def FetchFinaReport(
            self, context: FetchContext, stock_code: str, report_period: str, extensions: [str],
            date_from: [str], date_to: [str], extra_param=None) -> pd.DataFrame:
        return self.__safe_dynamic_run(context, 'FetchFinaReport', stock_code,
                                       report_period, extensions, date_from, date_to, extra_param)

    # --------------------------------------- Execute ---------------------------------------

    def __safe_dynamic_run(self, context: FetchContext, function_name: str, *args) -> object:
        dc_run_list = self.__pickup_execute_list(function_name, context)
        if len(dc_run_list) == 0:
            print('No data collector support this function: ' + function_name + '()')
            return None
        return self.__safe_execute_list(dc_run_list, function_name, context, *args)

    def __pickup_execute_list(self, function_name: str, context: FetchContext) -> [object]:
        if function_name == '' or context is None:
            return None
        exe_spec = ''
        exe_last = ''
        exe_after = ''
        lr = context.GetLastInvokingResult()

        if lr is not None:
            exe_last = lr.Plugin
        if context.ExecuteMode == FetchContext.EXE_SPECIFIED:
            exe_spec = context.SpecifiedPlugin
        elif context.ExecuteMode == FetchContext.EXE_AGAIN:
            exe_spec = exe_last
        if context.ExecuteMode == FetchContext.EXE_CONTINUE:
            exe_after = exe_last

        dc_run_list = []
        dc_list = self.__collector_loader.GetModules()
        for dc in dc_list:
            # Only execute the plug-in after the one specified
            if exe_after != '':
                if dc.PluginName == exe_after:
                    exe_after = ''
                continue
            # Check specified plug-in -- from context
            if exe_spec != '':
                if dc.PluginName != exe_spec:
                    continue
                else:
                    dc_run_list.append(dc.Inst)
                    break
            # Check plug-in status -- from context
            invoking_status = context.GetInvokingState(function_name, dc.PluginName)
            if invoking_status in [FetchContext.RST_EXCLUDE,
                                   FetchContext.RST_NOT_ACCEPT,
                                   FetchContext.RST_NO_SUCH_FUNCTION]:
                continue
            # Check function existence -- from module
            if not module_manager.IsFunctionExists(dc.Inst, function_name):
                context.UpdateInvokingResult(function_name, dc.PluginName,
                                             None, FetchContext.RST_NO_SUCH_FUNCTION)
                continue
            dc_run_list.append(dc.Inst)
        return dc_run_list

    def __safe_execute_list(self, dc_run_list: [object], function_name: str, context: FetchContext, *args) -> object:
        return_obj = None
        for dc in dc_run_list:
            try:
                func = getattr(dc, function_name)
                return_obj = func(*args)
                # Record invoking result
                if return_obj is not None:
                    status = FetchContext.RST_OK
                else:
                    status = FetchContext.RST_FAIL
                context.UpdateInvokingResult(function_name, dc.Name(), return_obj, status)
                # If not EXE_ALL mode. Just return the first successful one.
                if context.ExecuteMode != FetchContext.EXE_ALL and return_obj is not None:
                    break
            except Exception as e:
                context.UpdateInvokingResult(function_name, dc.Name(), None, FetchContext.RST_FAIL)
                print("Function run fail.")
                print('Error =>', e)
                print('Error =>', traceback.format_exc())
            finally:
                pass
        return return_obj


# class Collector_StockHis_Yahoo:
#     def Fetch(self, stock_code : str) -> pd.DataFrame:
#         market = self.GetStockMarket(stock_code)
#         if market is None:
#             return None
#         url = 'http://table.finance.yahoo.com/table.csv?s=' + stock_code + '.' + market
#         df = Utiltity.common.DownloadCsvAsDF(url)
#         df.columns = df.columns.map(lambda x: x.replace(' ', '_'))
#         return df
#
#     def GetStockMarket(self, stock):
#         if len(stock) != 6:
#             return ''
#         if stock[0:2] == '00' or stock[0:3] == '200' or stock[0:3] == '300':
#             return 'sz'
#         if stock[0:2] == '60' or stock[0:3] == '900':
#             return 'ss'
#         return ''

