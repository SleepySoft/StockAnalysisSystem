#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:YuQiu
@time: 2017/09/01
@file: strategy_manager.py
@function:
@modify:
"""
import traceback

from Recycled import module_manager


class StrategyReport:

    class ReportData:
        def __init__(self):
            self.Grade = 0
            self.Values = {}
            self.Comment = ''
            self.Judgement = False
            self.StockCode = ''
            self.StrategyName = ''

    def __init__(self):
        self.__report = {}

    def Dump(self):
        pass

    # score : 0 - 100
    def Grade(self, strategy_name: str, stock_code: str, score: int):
        self.__get_report(strategy_name, stock_code).Grade = score

    def Storage(self, strategy_name: str, stock_code: str, key: str, value: str):
        self.__get_report(strategy_name, stock_code).Values[key] = value

    # comments: Any text.
    def Comment(self, strategy_name: str, stock_code: str, comments: str):
        self.__get_report(strategy_name, stock_code).Comment = comments

    # qualified: True - pass; False - Fail
    def Judgement(self, strategy_name: str, stock_code: str, qualified: bool):
        self.__get_report(strategy_name, stock_code).Judgement = qualified

    # --------------------------------- private ---------------------------------

    def __get_report(self, strategy_name: str, stock_code: str) -> ReportData:
        stock_reports = self.__report.get(stock_code, None)
        if stock_reports is None:
            stock_reports = map()
            self.__report[stock_code] = stock_reports
        stock_strategy_report = stock_reports.get(strategy_name, None)
        if stock_strategy_report is None:
            stock_strategy_report = StrategyReport.ReportData()
            stock_strategy_report.StockCode = stock_code
            stock_strategy_report.StrategyName = strategy_name
            stock_reports[strategy_name] = stock_strategy_report
        return stock_strategy_report


class IStrategy:
    def Instructions(self) -> str:
        return ''

    def Analysis(self, strategy_report: StrategyReport) -> bool:
        return False


class StrategyManager:
    def __init__(self):
        self.__strategy_loader = module_manager.ModuleManager()

    def Init(self):
        return self.__strategy_loader.LoadModuleFromFolder('strategy')

    def ReloadStrategy(self) -> bool:
        return self.__strategy_loader.LoadModuleFromFolder('strategy')

    def GetStrategyNameList(self) -> [str]:
        return [m.PluginName for m in self.__strategy_loader.GetModules()]

    def GetStrategyInstructions(self, strategies: str) -> str:
        for m in self.__strategy_loader.GetModules():
            if m.Name() == strategies:
                return m.Instructions()
        return None

    def ExecuteStrategy(self, strategies: [str] = None) -> StrategyReport:
        if strategies is not None and len(strategies) > 0:
            strategy_list = self.__strategy_loader.PickupModules(strategies)
        else:
            strategy_list = self.__strategy_loader.GetModules()
        strategy_report = StrategyReport()
        strategy_list_sort = self.__strategy_loader.SortModules(strategy_list)
        self.__safe_dynamic_run(strategy_list_sort, strategy_report)
        return strategy_report

    # --------------------------------------- private ---------------------------------------

    def __safe_dynamic_run(self, strategy_list: [str], strategy_report: StrategyReport):
        for dc in strategy_list:
            try:
                func = getattr(dc, 'Analysis')
                func(strategy_report)
            except Exception as e:
                print("Function run fail.")
                print('Error =>', e)
                print('Error =>', traceback.format_exc())
            finally:
                pass