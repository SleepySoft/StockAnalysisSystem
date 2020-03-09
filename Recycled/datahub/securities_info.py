import logging
import traceback
import pandas as pd

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    import DataHub.DataUtility as DataUtility
    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Database.UpdateTableEx import UpdateTableEx
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
except Exception as e:
    sys.path.append(root_path)

    import DataHub.DataUtility as DataUtility
    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Database.UpdateTableEx import UpdateTableEx
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
finally:
    logger = logging.getLogger('')


NEED_COLLECTOR_CAPACITY = [
    'SecuritiesInfo',
]
SECURITIES_EXCHANGE = ['SSE', 'SZSE']
TABLE_SECURITIES_INFO = 'SecuritiesInfo'
IDENTITY_SECURITIES_INFO = '<stock_code>.<exchange>'
FIELD_INFO = {'code':           (['str'], []),
              'name':           (['str'], []),
              'area':           (['str'], []),
              'industry':       (['str'], []),
              'fullname':       (['str'], []),
              'en_name':        (['str'], []),
              'market':         (['str'], []),
              'exchange':       (['str'], ['SSE', 'SZSE']),
              'currency':       (['str'], []),
              'list_status':    (['int'], []),
              'listing_date':   (['datetime'], []),
              'delisting_date': (['datetime'], []),
              'stock_connect':  (['int'], [])
              }


class SecuritiesInfo(DataUtility.DataUtility):
    def __init__(self, plugin: PluginManager, update: UpdateTableEx):
        super().__init__(plugin, update)
        self.__cached_data = None
        self.__load_cached_data()

    # ------------------------------------------------- Extend Feature -------------------------------------------------

    def get_stock_list(self, exchange: list or str = None) -> [(str, str)]:
        df = self.__cached_data
        if exchange is not None and len(exchange) > 0:
            if isinstance(exchange, str):
                exchange = [exchange]
            df = df[df['exchange'].isin(exchange)]
        code_list = df['code'].values.tolist()
        return code_list

    def get_stock_name(self, stock_code: str) -> [str]:
        df = self.__cached_data
        df = df[df['code'].str.contains(stock_code)]
        return df.name.tolist()

    def get_stock_code(self, stock_name: str) -> [str]:
        df = self.__cached_data
        df = df[df['name'].str.contains(stock_name)]
        return df.code.tolist()

    # ---------------------------------------------------------------------------------x--------------------------------

    def execute_update_patch(self, patch: DataUtility.Patch) -> DataUtility.RESULT_CODE:
        logger.info('SecuritiesInfo.execute_update_patch(' + str(patch) + ')')

        df = self.__do_fetch_securities_info(patch.tags)
        if df is None or len(df) == 0:
            return DataUtility.RESULT_FAILED
        df.reindex()
        self.__cached_data = df
        return DataUtility.RESULT_SUCCESSFUL

    def trigger_save_data(self, patch: DataUtility.Patch) -> DataUtility.RESULT_CODE:
        nop(patch)
        if self.__save_cached_data():
            return self.get_update_table().update_latest_update_time(['SecuritiesInfo'])
        return DataUtility.RESULT_FAILED

    # --------------------------------------------------- private if ---------------------------------------------------

    def data_from_cache(self, selectors: DataUtility.Selector or [DataUtility.Selector]) -> pd.DataFrame or None:
        nop(selectors)
        return self.__cached_data

    # -------------------------------------------------- probability --------------------------------------------------

    def get_reference_data_range(self, tags: [str]) -> (datetime.datetime, datetime.datetime):
        nop(self, tags)
        return [None, None]

    # -----------------------------------------------------------------------------------------------------------------

    def __do_fetch_securities_info(self, tags: [str]) -> pd.DataFrame:
        plugins = self.get_plugin_manager().find_module_has_capacity('SecuritiesInfo')
        for plugin in plugins:
            df = self.get_plugin_manager().execute_module_function(plugin, 'fetch_data', {
                'content': 'SecuritiesInfo',
                'exchange': tags
            })

            if not self._check_dataframe_field(df, FIELD_INFO, ['code', 'exchange']) or len(df) == 0:
                logger.info('SecuritiesInfo - Fetch data format Error.')
                continue
            return df
        return None

    def __load_cached_data(self) -> bool:
        table = DatabaseEntry().get_securities_table()
        record = table.query()
        if record is not None and len(record) > 0:
            self.__cached_data = pd.DataFrame(record)
            del self.__cached_data['DateTime']
            del self.__cached_data['_id']
        else:
            self.__cached_data = pd.DataFrame(column=list(FIELD_INFO.keys()))
        return True

    def __save_cached_data(self) -> bool:
        table = DatabaseEntry().get_securities_table()
        for index, row in self.__cached_data.iterrows():
            code = row['code']
            exchange = row['exchange']
            identity = IDENTITY_SECURITIES_INFO.\
                replace('<stock_code>', code).\
                replace('<exchange>', exchange)
            table.upsert(identity, text_auto_time('2000-01-01'), row.to_dict())
        return True


# ----------------------------------------------------- Test Code ------------------------------------------------------


def __build_instance() -> SecuritiesInfo:
    from os import path
    root_path = path.dirname(path.dirname(path.abspath(__file__)))
    plugin_path = root_path + '/Collector/'

    collector_plugin = PluginManager(plugin_path)
    collector_plugin.refresh()

    update_table = UpdateTableEx()

    return SecuritiesInfo(collector_plugin, update_table)


def test_basic_feature():
    si = __build_instance()
    df = si.query_data('')
    print(df)
    print('-------------------------------------------------------------------------------')


def test_extra_function():
    si = __build_instance()

    stocks = si.get_stock_list()
    assert(3000 < len(stocks) < 4000)
    print(stocks)
    print('Stock Count :' + str(len(stocks)))
    print('-------------------------------------------------------------------------------')

    stock_codes = si.get_stock_code('浦发银行')
    assert(len(stock_codes) == 1 and stock_codes[0] == '600000')

    stock_codes = si.get_stock_code('银行')
    print(stock_codes)
    print('Bank stock Count :' + str(len(stock_codes)))
    print('-------------------------------------------------------------------------------')

    assert(len(stock_codes) > 4)
    assert('601398' in stock_codes)
    assert('601288' in stock_codes)
    assert('601328' in stock_codes)
    assert('601939' in stock_codes)
    assert('000001' in stock_codes)
    assert('002142' in stock_codes)

    stock_names = si.get_stock_name('601398')
    assert(len(stock_names) == 1 and stock_names[0] == '工商银行')

    stock_name = si.get_stock_name('600')
    print(stock_name)
    print('Stock that includes "600" count :' + str(len(stock_name)))
    print('-------------------------------------------------------------------------------')

    assert('浦发银行' in stock_name)
    assert('工商银行' not in stock_name)


def test_entry():
    test_basic_feature()
    test_extra_function()


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







