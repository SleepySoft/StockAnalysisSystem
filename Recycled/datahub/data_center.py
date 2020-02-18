#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2017/08/09
@file: data_center.py
@function:
@modify:
"""

import pandas as pd
import json

from Recycled import data_collector
import Utiltity.common
import Utiltity.constant
import stock_analysis_system as sAs


class DataWeb:
    def Init(self) -> bool:
        return True

    # Return: map(), not None
    #   Key: str -> Utiltity.constant.ANNUAL_REPORT_TYPES
    #   Value: DataFrame -> Columns: ......; Index: Year/Date; Cell: Currency unit in CNY Yuan
    @staticmethod
    def DownloadStockAnnualFinaData(stock_code: str, annual_report_type: str) -> {str: pd.DataFrame}:
        ctx = data_collector.FetchContext()
        ar_dict = sAs.instance.GetDataCollector().FetchStockAnnualFinaData(
            ctx, stock_code, [annual_report_type, ], 0, 9999)
        if ar_dict is None or not isinstance(ar_dict, dict):
            print('Download annual report from data collector fail.')
            return {}
        # report = ar_dict.get(annual_report_type, None)
        # if report is None:
        #     print('DownloadAnnualReport() - Fail.')
        #     return None
        ar_dict_keys = ar_dict.keys()
        for k in ar_dict_keys:
            report_origin = ar_dict.get(k, None)
            report = DataWeb.__check_format_downloaded_annual_report(report_origin)
            if report is None:
                print('__check_format_downloaded_annual_report() - Error format of ' + k + ' and cannot recover.')
            ar_dict[k] = report
        return ar_dict

    # Return: DataFrame -> Columns may include but not limited to:
    #     company_name|stock_name_a|stock_code_a|stock_name_b|stock_code_b|industry
    #     english_name|reg_address|listing_date_a|listing_date_b
    #     area|provinces|city|web_address
    @staticmethod
    def DownloadStockIntroduction() -> pd.DataFrame:
        ctx = data_collector.FetchContext()
        ctx.SpecifyPlugin('MarketInformationFromSZSE')
        return sAs.instance.GetDataCollector().FetchStockIntroduction(ctx)

    # Return: pd.DataFrame
    #   Column:
    #       stock: str -> Stock code
    #       date: str of date -> 2010|2010-09|2010-09-08
    #       content: bytes -> File data
    @staticmethod
    def DownloadAnnualFinaReport(stock_code: str, extension: str, year_from: int, year_to: int):
        ctx = data_collector.FetchContext()
        return sAs.instance.GetDataCollector().FetchStockIntroduction(
            ctx, stock_code, 'annual', [extension, ], str(year_from), str(year_to))

    @staticmethod
    def __check_format_downloaded_annual_report(annual_report: pd.DataFrame) -> pd.DataFrame:
        if annual_report is None:
            return None

        # Check index: it should be year digit str.
        index_format = []
        index = annual_report.index.tolist()
        for i in index:
            if not isinstance(i, int) and not isinstance(i, str):
                return None
            if i is int:
                i = str(i)
            elif '-' in i:
                i = i.split('-')[0]
            if not i.isdigit():
                i = ''
                print('__check_format_downloaded_annual_report() - Warning: Invalid index : ', i)
            index_format.append(i)
        annual_report.index = index_format

        # standardize columns
        columns = annual_report.columns.tolist()
        columns = sAs.instance.GetAliasesTable().standardize(columns)
        annual_report.columns = columns

        # Remove empty row
        annual_report = annual_report.loc[annual_report.index != '']
        # annual_report.to_csv('D:/test.csv')

        return annual_report


class DataDB:
    STOCK_INFORMATION_TABLE_DESC = [
        ['company_name', 'varchar(255)'],
        ['stock_name_a', 'varchar(16)'],
        ['stock_code_a', 'varchar(16)'],
        ['stock_name_b', 'varchar(16)'],
        ['stock_code_b', 'varchar(16)'],
        ['industry', 'varchar(100)'],

        ['area', 'varchar(100)'],
        ['city', 'varchar(100)'],
        ['provinces', 'varchar(100)'],
        ['web_address', 'varchar(100)'],

        ['reg_address', 'varchar(255)'],
        ['english_name', 'varchar(255)'],
        ['listing_date_a', 'date'],
        ['listing_date_b', 'date']
        ]

    FINANCIAL_STATEMENTS_TABLE = \
        'FinancialDataTable'
    FINANCIAL_STATEMENTS_FIELDS = [
        'stock_code',
        'report_type',
        'accounting_annual',
        'financial_data'
    ]
    FINANCIAL_STATEMENTS_TABLE_DESC = [
        ['serial', 'int'],
        ['stock_code', 'varchar(20)'],
        ['report_type', 'int'],
        ['accounting_annual', 'int'],
        ['financial_data', 'TEXT'],
    ]

    def __init__(self, data_web: DataWeb):
        self.__data_web = data_web

    def Init(self,) -> bool:
        execute_statues = True
        if sAs.instance.GetDataCenterDB().TableExists(
                DataDB.FINANCIAL_STATEMENTS_TABLE):
            execute_statues = sAs.instance.GetDataCenterDB().CreateTable(
                DataDB.FINANCIAL_STATEMENTS_TABLE,
                DataDB.FINANCIAL_STATEMENTS_TABLE_DESC) and execute_statues
        if not execute_statues:
            print('DataDB : Financial Statement Table Create Fail!')
            return False
        return True

    def QueryStockInformation(self) -> pd.DataFrame:
        df = sAs.instance.GetDataCenterDB().DataFrameFromDB('StockInformation', [])
        if df is None:
            df = self.__data_web.DownloadStockIntroduction()
            if df is not None:
                sAs.instance.GetDataCenterDB().DataFrameToDB('StockInformation', df)
        return df

    # Return value: None if fail
    def QueryAnnualReport(self, stock_code: str, year_from: int, year_to: int) -> pd.DataFrame:
        condition = " stock_code = '" + stock_code + "'"
        year_begin, year_end = Utiltity.common.correct_start_end(
            year_from, year_to, 2000, Utiltity.common.Date()[0])
        condition += ' AND accounting_annual >= ' + str(year_begin) + ' AND accounting_annual <= ' + str(year_end)
        ar_dict = self.__query_annual_report(DataDB.FINANCIAL_STATEMENTS_TABLE, condition)
        df = ar_dict.get(stock_code, None)
        if df is None:
            df = self.__download_store_annual_report(stock_code)
        return df

    def __download_store_annual_report(self, stock_code: str):
        df = pd.DataFrame()
        ar_dict = self.__data_web.DownloadStockAnnualFinaData(stock_code, 'all')
        if ar_dict is None or len(ar_dict) == 0:
            print('Get annual report from DataWeb is empty.')
            return df
        for k in ar_dict.keys():
            report = ar_dict.get(k, None)
            if report is not None:
                self.__store_annual_report(stock_code, k, report)
                df = Utiltity.common.MergeDataFrameOnIndex(df, report)
        return df

    # -------------------------------------- private --------------------------------------

    # Not use EAV, use JSON.
    def __store_annual_report(self, stock_code: str, report_type: str, annual_report: pd.DataFrame) -> bool:
        if annual_report is None:
            return False
        report_type_enum = Utiltity.constant.annual_report_type2enum(report_type)
        df_json = self.__annual_df_2_json_df(stock_code, report_type_enum, annual_report)
        if df_json is None or len(df_json) == 0:
            return False
        # Not need to insert serial number
        df_json.columns = DataDB.FINANCIAL_STATEMENTS_FIELDS
        self.__del_annual_report(stock_code, [report_type_enum], [])
        return sAs.instance.GetDataCenterDB().DataFrameToDB(
            DataDB.FINANCIAL_STATEMENTS_TABLE, df_json, 'append')

    def __query_annual_report(self, annual_report_table: str, condition: str) -> {str: pd.DataFrame}:
        annual_report = sAs.instance.GetDataCenterDB().DataFrameFromDB(
            annual_report_table, DataDB.FINANCIAL_STATEMENTS_FIELDS, condition)
        if annual_report is None or len(annual_report) == 0:
            return {}
        return self.__json_df_to_annual_df(annual_report)

    @staticmethod
    def __del_annual_report(stock_code: str, report_types: [int], annuals: [int]) -> bool:
        types = ','.join([str(t) for t in report_types])
        years = ','.join([str(y) for y in annuals])
        condition = "stock_code = '" + stock_code + "'"
        if types != '':
            condition += ' AND report_type IN (' + types + ')'
        if years != '':
            condition += ' AND accounting_annual IN (' + years + ')'
        return sAs.instance.GetDataCenterDB().ExecuteDelete(DataDB.FINANCIAL_STATEMENTS_TABLE, condition)

    # df <-> json
    @staticmethod
    def __annual_df_2_json_df(stock_code: str, report_type, df: pd.DataFrame) -> pd.DataFrame:
        lines = []
        columns = df.columns.tolist()
        columns = sAs.instance.GetAliasesTable().standardize(columns)
        for index, row in df.iterrows():
            line = []
            year = index.split('-')[0]
            line.append(stock_code)                 # The 1st column
            line.append(report_type)                # The 2nd column
            line.append(year)                       # The 3rd column
            properties = {}
            for r, c in zip(row, columns):
                properties[c] = r
            line.append(json.dumps(properties))     # The 4th column
            lines.append(line)
        return pd.DataFrame(lines)

    @staticmethod
    def __json_df_to_annual_df(df_json: pd.DataFrame) -> {str: pd.DataFrame}:
        if DataDB.FINANCIAL_STATEMENTS_FIELDS[0] not in df_json.columns or\
            DataDB.FINANCIAL_STATEMENTS_FIELDS[2] not in df_json.columns or\
                DataDB.FINANCIAL_STATEMENTS_FIELDS[3] not in df_json.columns:
            return {}
        df_trim = df_json[[DataDB.FINANCIAL_STATEMENTS_FIELDS[0],       # stock_code -> #0
                           DataDB.FINANCIAL_STATEMENTS_FIELDS[2],       # accounting_annual -> #1
                           DataDB.FINANCIAL_STATEMENTS_FIELDS[3]]]      # financial_data -> #2
        map_stock_prop = {}
        for index, row in df_trim.iterrows():
            stock_code = row[0]
            accounting_annual = row[1]
            financial_data = row[2]

            map_properties = map_stock_prop.get(stock_code, None)
            if map_properties is None:
                map_properties = {}
                map_stock_prop[stock_code] = map_properties

            properties = json.loads(financial_data)
            exist_properties = map_properties.get(accounting_annual, None)
            if exist_properties is not None:
                exist_properties.update(properties)
            else:
                map_properties[accounting_annual] = properties

        map_df_stocks = {}
        for stock_code in map_stock_prop.keys():
            map_properties = map_stock_prop.get(stock_code)
            for annual in map_properties:
                properties = map_properties.get(annual, None)
                properties['accounting_annual'] = accounting_annual
                df_line = pd.DataFrame([properties], columns=properties.keys())
                df_line.set_index('accounting_annual', inplace=True)

                df_exists = map_df_stocks.get(stock_code, None)
                if df_exists is not None:
                    map_df_stocks[stock_code] = df_exists.append(df_line)
                else:
                    map_df_stocks[stock_code] = df_line
        for stock_code in map_df_stocks.keys():
            df = map_df_stocks.get(stock_code)
            if df is not None and 'accounting_annual' in df.columns.tolist():
                df.set_index('accounting_annual', inplace=True)
                df.sort_index(inplace=True)

        # for k in map_df_stocks.keys():
        #     df_ref = map_df_stocks.get(k)
        #     df_ref.set_index('accounting_annual', inplace=True, drop=True)
            # df_ref.columns = sAs.GetInstance.GetAliasesTable().Readablize(df_ref.columns.tolist())
        return map_df_stocks


class DataCache:

    def __init__(self, data_db: DataDB):
        self.__data_db = data_db
        self.__cached_stock_info = None
        self.__cached_stock_table = {}
        self.__cached_annual_report = {}

    def Init(self) -> bool:
        return True

    def GetStockTable(self) -> dict:
        if self.__cached_stock_table is None or len(self.__cached_stock_table) == 0:
            self.__cache_stock_information()
        return self.__cached_stock_table

    def GetStockInformation(self) -> pd.DataFrame:
        if self.__cached_stock_info is None or len(self.__cached_stock_info) == 0:
            self.__cache_stock_information()
        return self.__cached_stock_info

    def GetAnnualFinaReport(self, stock_code: str, year_from: int, year_to: int) -> pd.DataFrame:
        df = self.__cached_annual_report.get(stock_code, None)
        year_start, year_end = Utiltity.common.correct_start_end(
            year_from, year_to, 2000, Utiltity.common.Date()[0])
        if df is not None:
            missing_year = Utiltity.common.set_missing(range(year_start, year_end), df.index)
            if len(missing_year) == 0:
                return df.loc[year_start: year_end]
        df = self.__cache_annual_report(stock_code, year_start, year_end)
        return df

    # ---------------------------------------- private ----------------------------------------

    def __cache_stock_information(self):
        self.__cached_stock_info = self.__data_db.QueryStockInformation()
        if self.__cached_stock_info is not None:
            self.__cached_stock_table = self.__cached_stock_info.set_index('stock_code_a')['stock_name_a'].to_dict()

    def __cache_annual_report(self, stock_code: str, year_from: int, year_to: int) -> pd.DataFrame:
        df = self.__data_db.QueryAnnualReport(stock_code, year_from, year_to)
        if df is None or len(df) == 0:
            print('Get annual report from DataDB is empty.')
        exist_df = self.__cached_annual_report.get(stock_code, None)
        if exist_df is None:
            self.__cached_annual_report[stock_code] = df
        else:
            self.__cached_annual_report[stock_code] = pd.concat([exist_df, df], axis=1)
        return df


class DataCenter:

    def __init__(self):
        self.__data_web = DataWeb()
        self.__data_db = DataDB(self.__data_web)
        self.__data_cache = DataCache(self.__data_db)

    def Init(self) -> bool:
        ret = True
        ret &= self.__data_web.Init()
        ret &= self.__data_db.Init()
        ret &= self.__data_cache.Init()
        return ret

    # Return : map
    #    Key -> Stock code
    #    Value -> Stock name
    def GetStockTable(self) -> {str, str}:
        return self.__data_cache.GetStockTable()

    # return -> DataFrame
    def GetStockAnnualReportData(self,
                                 stock_code: str, accounting: [str], year_from: int, year_to: int) -> pd.DataFrame:
        year_start, year_end = Utiltity.common.correct_start_end(year_from, year_to, 2000, Utiltity.common.Date()[0])
        account_s = sAs.instance.GetAliasesTable().standardize(accounting)
        if len(account_s) > 0:
            df_stock = pd.DataFrame(columns=account_s)
        else:
            df_stock = None
        report = self.__data_cache.GetAnnualFinaReport(stock_code, year_start, year_end)
        if report is None or len(report) == 0:
            print('Get annual report from DataCache is empty.')
        if report is not None:
            if df_stock is not None:
                Utiltity.common.DataFrameColumnCopy(report, df_stock, account_s)
            else:
                df_stock = report

            print(df_stock)

            if len(accounting) > 0:
                df_stock.columns = accounting
            if len(df_stock) > 0:
                df_stock.index = report.index
                df_stock.sort_index(inplace=True)
                df_stock.convert_objects(convert_numeric=True)
            return df_stock
        return None


































































    # def __get_annual_report(self, stock_code: str, annual_report_type: str, condition: str) -> pd.DataFrame:
    #     # 1.Query
    #     result = self.__query_annual_report(annual_report_type, condition)
    #     if result is not None and len(result) > 0:
    #         return result.get(stock_code, None)
    #
    #     # 2.Download
    #     ar_dict = self.__download_annual_report(stock_code, annual_report_type)
    #     if ar_dict is None or not isinstance(ar_dict, dict):
    #         print('__download_annual_report() : Wrong result - ', type(ar_dict))
    #         return None
    #     report = ar_dict.get(annual_report_type, None)
    #     if report is None:
    #         print('__get_annual_report() - Fail.')
    #         return None
    #
    #     # 3.Format
    #     report = self.__check_format_downloaded_annual_report(report)
    #     if report is None:
    #         print('__check_format_downloaded_annual_report() - Error format of annual report and cannot recover.')
    #         return None
    #
    #     # 4.Save
    #     self.__save_annual_report(stock_code, report, annual_report_type)
    #
    #     return report
    #
    # def CacheAnnualReportData(self, stock_codes: [str]):
    #     for stock in stock_codes:
    #         self.__cache_annual_report[stock] = \
    #             self.__core.GetStockAnnualReportData(
    #             stock, 0, 0, Utiltity.constant.ANNUAL_REPORT_TYPES)



    # def DownloadAnnualReportPDF(self, root_path: str, stock_codes: [str], annual: [int]):
    #     ctx = data_collector.FetchContext()
    #     sAs.GetInstance.GetDataCollector().DownloadStockAnnualReport(
    #         ctx,
    #     )
    #
    # # --------------------------------------- private ---------------------------------------
    #
    # def __get_cached_stock_data(self, stock_code: str) -> {str: pd.DataFrame}:
    #     return self.__cache_annual_report.get(stock_code, None)
    #
    # # report_type -> Utiltity.constant.ANNUAL_REPORT_TYPES
    # def __get_cached_stock_annual_report(self, stock_code: str, report_type: str) -> pd.DataFrame:
    #     tables = self.__cache_annual_report.get(stock_code, None)
    #     if tables is None:
    #         return None
    #     return tables.get(report_type, None)

    # # For test
    # @staticmethod
    # def SubAnnualReportTable(df: pd.DataFrame, years: [int], accounting: [str]) -> pd.DataFrame:
    #     return DataCenter.__sub_annual_report_table(df, years, accounting)

    # @staticmethod
    # def __sub_annual_report_table(df: pd.DataFrame, years: [int], accounting: [str]) -> pd.DataFrame:
    #     df_sub = pd.DataFrame()
    #     for a in accounting:
    #         if a not in df.columns:
    #             serial = np.empty(df.shape[0])
    #             serial.fill(np.nan)
    #         else:
    #             serial = df[a]
    #         df_sub.insert(len(df_sub.columns), a, serial)
    #     return df_sub.loc[years]

