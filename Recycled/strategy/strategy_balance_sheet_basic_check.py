#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2017/09/01
@file: strategy_balance_sheet_basic_check.py
@function:
@modify:
"""


import pandas as pd

from Recycled import strategy_manager as sm


class BalanceSheetBasicCheck:

    def __init__(self):
        self.__sas = None

    def Name(self) -> str:
        return 'BalanceSheetBasicCheck'
    def Depends(self) -> [str]:
        return []
    def SetEnvoriment(self, sAs):
        self.__sas = sAs

    def Instructions(self) -> str:
        return ''

    def Analysis(self, strategy_report: sm.StrategyReport) -> bool:
        self.__check_1('002184')
        return True

    # 检查应收
    def __check_1(self, stock_code: str):
        dc = self.__sas.GetDataCenter()
        df = dc.GetStockAnnualReportData(stock_code, ['营业收入', '应收票据', '应收账款', '其他应收款'], 2005, 2009)
        if df is None:
            return
        print(df)

        df_relative = pd.DataFrame()
        for c in df.columns.tolist():
            if c != '营业收入':
                df_relative[c] = df[c] / df['营业收入']
        df_relative_pct_change = df_relative.pct_change()
        print(df_relative_pct_change)

        # df_ratio = pd.DataFrame()
        # for c in df.columns.tolist():
        #     if c != '流动资产合计':
        #         df_ratio[c] = df[c] / df['流动资产合计']
        #     else:
        #         df_ratio[c] = df[c]
        # df_ratio.index = df.index
        # print(df_ratio)

        df_pct_change = df.pct_change()
        print(df_pct_change)

    # 检查费用
    def __check_2(self, stock_code: str):
        dc = self.__sas.GetDataCenter()
        dc.GetStockAnnualReportDataTable(stock_code, ['销售费用'], ['管理费用'], ['财务费用'])


def GetModuleClass() -> object:
    return BalanceSheetBasicCheck
