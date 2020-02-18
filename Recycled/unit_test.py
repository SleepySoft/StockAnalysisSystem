#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2017/09/07
@file: unit_test.py
@function:
@modify:
"""


import traceback
import requests

import stock_analysis_system as sAs


# def test_sub_dataframe():
#     df = pd.DataFrame({
#         'column1': range(100, 105),
#         'column2': range(300, 305),
#         'column3': range(500, 505)
#     })
#     df = df.set_index([[2001, 2002, 2003, 2005, 2006]])
#     print(df)
#
#     # df = dc.DataCenter.SubAnnualReportTable(df, [2001, 2003], ['column2', 'column3'])
#     df = dc.DataCenter.SubAnnualReportTable(df, [2001, 2004, 2005], ['column1', 'column4'])
#     print(df)


def test__AliasesTable_ExportTable():
    sAs.instance.GetAliasesTable().ExportTable('D:/AliasesTable.csv')


def test_run_strategy():
    all_strategy = sAs.instance.GetStrategyManager().GetStrategyNameList()
    sAs.instance.GetStrategyManager().ExecuteStrategy(all_strategy)


def test_fetch_annual_pdf_from_szse():
    url = 'http://disclosure.szse.cn/m/search0425.jsp'
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'}
    payload = {
        'leftid': '1',
        'lmid': 'drgg',
        'pageNo': '1',
        'stockCode': '002184',
        'keyword': '',
        'noticeType': '010301',
        'startTime': '2011-01-01',
        'endTime': '2017-09-01',
        'imageField.x': '23',
        'imageField.y': '8',
        'tzy': '',
    }
    r = requests.post(url, headers=headers, data=payload)
    with open("d:/example.html", 'wb') as file:
        file.write(r.content)
    print(r.content.decode('gb2312'))


# def test__StockFinancialDataFromSZSE():
#     import Collector.stock_fina_szse as sf
#     # sf.StockFinancialDataFromSZSE().TestWithFile('D:/example.html')
#     sf.DownloadStockAnnualReport()


def main():
    sAs.instance.init()
    # test__DataCenter_GetStockTable()  # <- Passed on 20171012
    # test__AliasesTable_ExportTable()  # <- Passed on 20171012

    # test_fetch_annual_pdf_from_szse()
    # test__StockFinancialDataFromSZSE()

    test_run_strategy()

    # df = pd.DataFrame({
    #     'a': [100, 200, 300, 400, 500],
    #     'b': [1.0, 2.0, 3.0, 4.0, 5.0]
    # }, index=[1, 2, 3, 4, 5])
    # print(df)

    # df2 = df.pct_change()
    # print(df2)

# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass
