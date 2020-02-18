#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:YuQiu
@time: 2017/08/14
@file: stock_info_szse.py
@function:
@modify:
"""

import pandas as pd
import Utiltity.common
from io import BytesIO
from openpyxl import load_workbook


class MarketInformationFromSZSE:

    def Name(self) -> str:
        return 'MarketInformationFromSZSE'
    def Depends(self) -> [str]:
        return []
    def SetEnvoriment(self, sAs):
        pass

    # Download excel from www.szse.cn
    def FetchStockIntroduction(self, extra_param=None) -> pd.DataFrame:
        content = Utiltity.common.Download('http://www.szse.cn/szseWeb/ShowReport.szse?SHOWTYPE=xlsx&CATALOGID=1110&tab1PAGENO=1&ENCODE=1&TABKEY=tab1')
        wb = load_workbook(filename=BytesIO(content))
        sheets = wb.get_sheet_names()
        sheet0 = sheets[0]
        ws = wb.get_sheet_by_name(sheet0)
        if ws is None:
            return None

        rows = ws.rows
        # columns = ws.columns

        content = []
        for row in rows:
            line = [col.value for col in row]
            content.append(line)

        df = pd.DataFrame(content)
        df.columns = df.iloc[0]
        df = df[1:]
        df.columns = ['stock_code', 'stock_name', 'company_name', 'english_name', 'reg_address',
                      'stock_code_a', 'stock_name_a', 'listing_date_a', 'total_equity_a', 'circulation_equity_a',
                      'stock_code_b', 'stock_name_b', 'listing_date_b', 'total_equity_b', 'circulation_equity_b',
                      'area', 'provinces', 'city', 'industry', 'web_address']
        return df


def GetModuleClass() -> object:
    return MarketInformationFromSZSE
