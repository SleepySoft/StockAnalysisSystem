#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2017/08/15
@file: stock_fina_163.py
@function:
@modify:
"""
import traceback
import numpy as np
import pandas as pd
import Utiltity.common
from io import BytesIO


class StockFinancialDataFrom163:

    def Name(self) -> str:
        return 'StockFinancialDataFrom163'
    def Depends(self) -> [str]:
        return []
    def SetEnvoriment(self, sAs):
        pass

    def FetchStockAnnualFinaData(
            self, stock_code: str, report_type: [str],
            year_from: int, year_to: int, extra_param=None) -> {str: pd.DataFrame}:
        result = {}
        if 'balance_sheet' in report_type or 'all' in report_type:
            url_balance_sheets = 'http://quotes.money.163.com/service/zcfzb_' + stock_code + '.html?type=year'
            df_balance_sheets = self.__fetch_from_163(url_balance_sheets)
            result['balance_sheet'] = self.__parse_to_yuan(df_balance_sheets)
        if 'income_statement' in report_type or 'all' in report_type:
            url_income_statement = 'http://quotes.money.163.com/service/lrb_' + stock_code + '.html?type=year'
            df_income_statement = self.__fetch_from_163(url_income_statement)
            result['income_statement'] = self.__parse_to_yuan(df_income_statement)
        if 'cash_flow_statement' in report_type or 'all' in report_type:
            url_cash_flow_statement = 'http://quotes.money.163.com/service/xjllb_' + stock_code + '.html?type=year'
            df_cash_flow_statement = self.__fetch_from_163(url_cash_flow_statement)
            result['cash_flow_statement'] = self.__parse_to_yuan(df_cash_flow_statement)
        return result

    def __fetch_from_163(self, url: str) -> pd.DataFrame:
        try:
            df = Utiltity.common.DownloadCsvAsDF(url, 'gb2312')
            df = df.T
            df.columns = df.iloc[0]
            df = df[1:]
            df.columns = df.columns.str.strip()
            df['报告日期'].replace('', np.nan, inplace=True)
            df.dropna(subset=['报告日期'], inplace=True)
            df.set_index('报告日期', inplace=True, drop=False)
            return df
        except Exception as e:
            print('Error =>', e)
            print('Error =>', traceback.format_exc())
            return None
        finally:
            pass

    def __parse_to_yuan(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None:
            return None
        columns = []
        for c in df.columns.tolist():
            if c.find('(万元)') >= 0 or c.find('（万元）') >= 0:
                columns.append(c.replace('(万元)', '').replace('（万元）', ''))
                # TODO: Distinguish empty and zero
                column = df[c].map(lambda a: str(Utiltity.common.str2float_safe(a, 0.0) * 10000))
                df[c] = column
            else:
                columns.append(c)
        df.columns = columns
        return df

def GetModuleClass() -> object:
    return StockFinancialDataFrom163
