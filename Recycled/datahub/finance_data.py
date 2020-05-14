import logging
import traceback
import pandas as pd

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    import Database.NoSqlRw as NoSqlRw
    import DataHub.DataUtility as DataUtility
    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Database.DatabaseEntry import DatabaseEntry
    from Database.UpdateTableEx import UpdateTableEx
    from Utiltity.plugin_manager import PluginManager
except Exception as e:
    sys.path.append(root_path)

    import Database.NoSqlRw as NoSqlRw
    import DataHub.DataUtility as DataUtility
    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Database.DatabaseEntry import DatabaseEntry
    from Database.UpdateTableEx import UpdateTableEx
    from Utiltity.plugin_manager import PluginManager
finally:
    logger = logging.getLogger('')


"""
We don't need to specify the filed currently. Just using the alias table.
If we want to standardize the field. Just rename all the fields.
"""


NEED_COLLECTOR_CAPACITY = ['BalanceSheet', 'CashFlowStatement', 'IncomeStatement']
ROOT_TAGS = ['BalanceSheet', 'CashFlowStatement', 'IncomeStatement']

TABLE_BALANCE_SHEET = 'BalanceSheet'
TABLE_CASH_FLOW_STATEMENT = 'CashFlowStatement'
TABLE_INCOME_STATEMENT = 'IncomeStatement'
TABLE_LIST = [TABLE_BALANCE_SHEET, TABLE_CASH_FLOW_STATEMENT, TABLE_INCOME_STATEMENT]

IDENTITY_FINANCE_DATA = '<stock_code>.<exchange>'

QUERY_FIELD = {
    'content':          ([str], ROOT_TAGS),
    'stock_identity':   ([str], []),
    # 'report_type':      ([str], ['ANNUAL', 'SEMIANNUAL', 'QUARTERLY', 'MONTHLY', 'WEEKLY']),
    'since':            ([datetime.datetime, None], []),
    'until':            ([datetime.datetime, None], [])}

RESULT_FIELD = {
    'identity':         (['str'], []),
    'period':           (['datetime'], [])}                # The last day of report period


class FinanceData(DataUtility.DataUtility):
    def __init__(self, plugin: PluginManager, update: UpdateTableEx):
        super().__init__(plugin, update)
        self.__cached_data = {
            'BalanceSheet': {},
            'IncomeStatement': {},
            'CashFlowStatement': {},
        }
        # key: report_type; value: stock_identity
        self.__save_table = {
            'BalanceSheet': [],
            'IncomeStatement': [],
            'CashFlowStatement': [],
        }

    # ------------------------------------------------------------------------------------------------------------------

    def execute_update_patch(self, patch: DataUtility.Patch) -> DataUtility.RESULT_CODE:
        logger.info('FinanceData.execute_update_patch(' + str(patch) + ')')

        if not self.is_data_support(patch.tags):
            logger.info('FinanceData.execute_update_patch() - Data is not support.')
            return DataUtility.RESULT_NOT_SUPPORTED

        report_type = patch.tags[0]
        save_list = self.__save_table.get(report_type)
        report_dict = self.__cached_data.get(report_type)

        if report_dict is None or save_list is None:
            # Should not reach here
            logger.error('Cannot not get report dict for ' + report_type)
            return DataUtility.RESULT_FAILED

        stock_identity = normalize_stock_identity(patch.tags[1])
        df = self.__do_fetch_finance_data(report_type, stock_identity, patch.since, patch.until)
        if df is None or len(df) == 0:
            return DataUtility.RESULT_FAILED

        # self.__alias_table.tell_names(list(df.columns))
        # self.__alias_table.check_save()

        # df.set_index('period')
        codes = df['identity'].unique()
        for code in codes:
            new_df = df[df['identity'] == code]
            if new_df is None or len(new_df) == 0:
                continue
            if code in report_dict.keys() and report_dict[code] is not None:
                old_df = report_dict[code]
                concated_df = concat_dataframe_row_by_index([old_df, new_df])
                report_dict[code] = concated_df
            else:
                report_dict[code] = new_df
            if code not in save_list:
                save_list.append(code)
        return DataUtility.RESULT_SUCCESSFUL

    def trigger_save_data(self, patches: [DataUtility.Patch]) -> DataUtility.RESULT_CODE:
        result = self.__save_cached_data()
        if result:
            if self.get_update_table().update_latest_update_time('SecuritiesInfo', '', ''):
                return DataUtility.RESULT_SUCCESSFUL
            else:
                return DataUtility.RESULT_FAILED
        return DataUtility.RESULT_FAILED

    # -------------------------------------------------- probability --------------------------------------------------

    def get_root_tags(self) -> [str]:
        nop(self)
        return NEED_COLLECTOR_CAPACITY

    def is_data_support(self, tags: [str]) -> bool:
        nop(self)
        return (tags is not None) and (isinstance(tags, list)) and (len(tags) > 2) and (tags[0] in ROOT_TAGS)

    def get_cached_data_range(self, tags: [str]) -> (datetime.datetime, datetime.datetime):
        if not self.is_data_support(tags):
            return None, None
        df = self.__cached_data.get(tags[0])
        if df is None or len(df) == 0:
            return None, None
        min_date = min(df['trade_date'])
        max_date = max(df['trade_date'])
        return text_auto_time(min_date), text_auto_time(max_date)

    # --------------------------------------------------- private if ---------------------------------------------------

    def data_from_cache(self, selector: DataUtility.Selector) -> pd.DataFrame or None:
        result = None
        if not self.is_data_support(selector.tags):
            logger.error('FinanceData.data_from_cache() - Error selector tags : ' + str(selector.tags))
            return None
        report_type = selector.tags[0]
        report_dict = self.__cached_data.get(report_type)
        if report_dict is None:
            logger.error('FinanceData.data_from_cache() - Do not support this kind of data : ' + report_type)
            return None
        stock_identity = selector.tags[1]
        stock_identity = normalize_stock_identity(stock_identity)
        stock_data = report_dict.get(stock_identity)
        if stock_data is None:
            self.__load_cached_data(selector.tags)
            stock_data = report_dict.get(stock_identity)
        if stock_data is None:
            return None
        df = slice_dataframe_by_datetime(stock_data, selector.since, selector.until)
        return df

    # -------------------------------------------------- probability --------------------------------------------------

    def get_reference_data_range(self, tags: [str]) -> (datetime.datetime, datetime.datetime):
        nop(self, tags)
        return [None, None]

    # -----------------------------------------------------------------------------------------------------------------

    def __do_fetch_finance_data(self, report_type: str, stock_identity: str,
                                report_since: datetime.datetime, report_until: datetime.datetime) -> pd.DataFrame:
        if report_type not in ROOT_TAGS:
            return None
        argv = {
                'content':          report_type,
                'stock_identity':   stock_identity,
                'since':            report_since,
                'until':            report_until,
            }
        if not self._check_dict_param(argv, QUERY_FIELD):
            return None
        plugins = self.get_plugin_manager().find_module_has_capacity(report_type)
        for plugin in plugins:
            df = self.get_plugin_manager().execute_module_function(plugin, 'fetch_data', argv)

            if df is None or not isinstance(df, pd.DataFrame) or len(df) == 0 or \
                    not self._check_dataframe_field(df, RESULT_FIELD, list(RESULT_FIELD.keys())):
                logger.info('Finance data - Fetch data format Error.')
                continue
            return df
        return None

    def __load_cached_data(self, tags: [str]) -> bool:
        report_type = tags[0]
        stock_identity = tags[1]
        data_table = DatabaseEntry().get_finance_table(report_type)
        record = data_table.query(stock_identity)
        if record is not None and len(record) > 0:
            df = pd.DataFrame(record)
            # del df['DateTime']
            del df['_id']
            self.__cached_data[report_type][stock_identity] = df
            return True
        else:
            logger.info('FinanceData.load_cached_data() - Not record for + ' + str(tags))
            return False

    def __save_cached_data(self) -> bool:
        for report_type in self.__save_table.keys():
            save_list = self.__save_table.get(report_type)
            data_table = DatabaseEntry().get_finance_table(report_type)
            for stock_identity in save_list:
                df = self.__cached_data.get(report_type).get(stock_identity)
                self.__save_single_data(stock_identity, df, data_table)

    def __save_single_data(self, stock_identity: str, df: pd.DataFrame, data_table: NoSqlRw.ItkvTable):
        nop(self)
        if 'period' not in df.columns:
            return False
        for index, row in df.iterrows():
            period = row['period']
            if isinstance(period, str):
                period = text_auto_time(period)
            data_table.upsert(stock_identity, period, row.to_dict())
        return True

    # --------------------------------------- interface of AliasTable.Participant --------------------------------------

    def name(self) -> str:
        return 'FinanceData'

    def get_using_names(self) -> [str]:
        names = []
        for table in TABLE_LIST:
            data_table = DatabaseEntry().get_finance_table(table)
            keys = data_table.get_all_keys()
            names.extend(keys)
        return list(set(names))

    def on_std_name_updating(self, old_name: str, new_name: str) -> (bool, str):
        nop(self)
        nop(old_name)
        nop(new_name)
        return True, ''

    def on_std_name_removed(self, name: str):
        for table in TABLE_LIST:
            data_table = DatabaseEntry().get_finance_table(table)
            data_table.remove_key(name)

    def on_std_name_updated(self, old_name: str, new_name: str):
        for table in TABLE_LIST:
            data_table = DatabaseEntry().get_finance_table(table)
            data_table.replace_key(old_name, new_name)

# ----------------------------------------------------- Test Code ------------------------------------------------------


def __build_instance() -> FinanceData:
    plugin_path = root_path + '/Collector/'

    collector_plugin = PluginManager(plugin_path)
    collector_plugin.refresh()

    update_table = UpdateTableEx()

    return FinanceData(collector_plugin, update_table)


def test_basic_feature():
    fd = __build_instance()

    df = fd.query_data(['BalanceSheet', '600000', 'ANNUAL'])
    print('----------------------------------------------------------------------------------------------')
    print(df)

    df = fd.query_data(['CashFlowStatement', '600000', 'ANNUAL'])
    print('----------------------------------------------------------------------------------------------')
    print(df)

    df = fd.query_data(['IncomeStatement', '600000', 'ANNUAL'])
    print('----------------------------------------------------------------------------------------------')
    print(df)


def test_entry():
    test_basic_feature()


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    test_entry()

    # If program reaches here, all test passed.
    print('All test passed.')


# ------------------------------------------------- Exception Handling -------------------------------------------------

def exception_hook(type, value, tback):
    # log the exception here
    print('Exception hook triggered.')
    print(type)
    print(value)
    print(tback)
    # then call the default handler
    sys.__excepthook__(type, value, tback)


if __name__ == "__main__":
    sys.excepthook = exception_hook
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass







