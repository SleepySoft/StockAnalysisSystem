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
    'TradeCalender',
]
TRADE_EXCHANGE = ['SSE', 'SZSE']
TABLE_TRADE_CALENDER = 'TradeCalender'
FIELD_TRADE_CALENDER = ['exchange', 'trade_date', 'status']
FIELD_TYPE_TRADE_CALENDER = ['object', 'datetime64[ns]', 'int64']


class TradeCalendar(DataUtility.DataUtility):
    def __init__(self, plugin: PluginManager, update: UpdateTableEx):
        super().__init__(plugin, update)
        self.__cached_data = {}
        self.__load_cached_data()

    # --------------------------------------------------- Interface ---------------------------------------------------

    def execute_update_patch(self, patch: DataUtility.Patch) -> DataUtility.RESULT_CODE:
        logger.info('TradeCalendar.execute_update_patch(' + str(patch) + ')')

        if not self.is_data_support(patch.tags):
            logger.info("TradeCalendar.execute_update_patch() - Not support tags: " + str(patch.tags))
            return None
        exchange = patch.tags[0]
        since, until = patch.since, patch.until
        if since is None:
            since = datetime.datetime(1990, 1, 1)
        if until is None:
            until = today()
        df = self.__do_fetch_trade_calender(exchange, since, until)
        if df is None:
            return DataUtility.RESULT_FAILED
        exists_df = self.__cached_data.get(exchange)
        if exists_df is not None:
            self.__cached_data[exchange] = concat_dataframe_row_by_index([exists_df, df])
        else:
            self.__cached_data[exchange] = df
        self.__cached_data[exchange].reindex()
        return DataUtility.RESULT_SUCCESSFUL

    def trigger_save_data(self, patch: DataUtility.Patch) -> DataUtility.RESULT_CODE:
        result = self.__save_cached_data()
        logger.info('TradeCalendar.trigger_save_data(' + str(patch) + ') - ' + str(result))
        return DataUtility.RESULT_SUCCESSFUL if result else DataUtility.RESULT_FAILED

    # --------------------------------------------------- private if ---------------------------------------------------

    def data_from_cache(self, selectors: DataUtility.Selector or [DataUtility.Selector]) -> pd.DataFrame or None:
        if not isinstance(selectors, list):
            selectors = [selectors]
        result = None
        for selector in selectors:
            if not self.is_data_support(selector.tags):
                return None
            df = self.__cached_data.get(selector.tags[0])
            if df is None:
                return None
            if selector.since is not None:
                df = df[df['trade_date'] >= selector.since]
            if selector.until is not None:
                df = df[df['trade_date'] <= selector.until]
            if result is None:
                result = df
            else:
                result = concat_dataframe_row_by_index([result, df])
        return result

    # -------------------------------------------------- probability --------------------------------------------------

    def get_root_tags(self) -> [str]:
        return TRADE_EXCHANGE

    def is_data_support(self, tags: str) -> bool:
        return len(tags) > 0 and tags[0] in TRADE_EXCHANGE

    def get_cached_data_range(self, tags: [str]) -> (datetime.datetime, datetime.datetime):
        if not self.is_data_support(tags):
            return None, None
        df = self.__cached_data.get(tags[0])
        if df is None or len(df) == 0:
            return None, None
        min_date = min(df['trade_date'])
        max_date = max(df['trade_date'])
        return text_auto_time(min_date), text_auto_time(max_date)

    # ---------------------------------------------------- private -----------------------------------------------------

    def __do_fetch_trade_calender(self, exchange: str, since: datetime.datetime, until: datetime.datetime):
        plugins = self.get_plugin_manager().find_module_has_capacity('TradeCalender')
        for plugin in plugins:
            df = self.get_plugin_manager().execute_module_function(plugin, 'fetch_data', {
                'content': 'TradeCalender',
                'exchange': exchange,
                'since': since,
                'until': until,
            })
            if df is not None and not isinstance(df, pd.DataFrame):
                logger.error('Fetched data is not a DataFrame.')
                continue
            if df is None or len(df) == 0:
                logger.error('Fetched data is empty.')
                continue
            if not self.__verify_fetching_data_format(df):
                logger.error('Format Error.')
                continue
            if since is not None:
                df = df.loc[df['trade_date'] >= since]
            if until is not None:
                df = df.loc[df['trade_date'] <= until]
            return df
        return None

    def __load_cached_data(self) -> bool:
        df = DatabaseEntry().get_utility_db().DataFrameFromDB('TradeCalender', FIELD_TRADE_CALENDER)
        if df is None:
            df = pd.DataFrame(columns=FIELD_TRADE_CALENDER)
        for exchange in TRADE_EXCHANGE:
            self.__cached_data[exchange] = df[df['exchange'] == exchange]
            self.__cached_data[exchange].reindex()
        return True

    def __save_cached_data(self) -> bool:
        first = True
        result = True
        for exchange in self.__cached_data.keys():
            df = self.__cached_data[exchange]
            if df is None or len(df) == 0:
                continue
            if_exists = 'replace' if first else 'append'
            first = False
            if DatabaseEntry().get_utility_db().DataFrameToDB('TradeCalender', df, if_exists):
                self._update_time_record(['TradeCalender', exchange], df, 'trade_date')
            else:
                result = False
        return result

    def __verify_fetching_data_format(self, df: pd.DataFrame):
        nop(self)
        if df is None:
            slog('Fetching data format error: Data is None')
            return False
        columns = list(df.columns)
        for field, field_type in zip(FIELD_TRADE_CALENDER, FIELD_TYPE_TRADE_CALENDER):
            if field not in columns:
                slog('Fetching data format error: Field is missing - ' + field)
                return False
            _type = df[field].dtype
            if _type != field_type:
                slog('Fetching data format error: Field type mismatch - ' + str(_type) + ' vs ' + str(field_type))
                return False
        continuity, min_date, max_date = check_date_continuity(df, 'trade_date')
        if not continuity:
            slog('Fetching data format error: Date is not continuity.')
            return False
        return True


# ----------------------------------------------------- Test Code ------------------------------------------------------


def __build_instance() -> TradeCalendar:
    from os import path
    root_path = path.dirname(path.dirname(path.abspath(__file__)))
    plugin_path = root_path + '/Collector/'

    collector_plugin = PluginManager(plugin_path)
    collector_plugin.refresh()

    update_table = UpdateTableEx()

    return TradeCalendar(collector_plugin, update_table)


def test_basic_feature():
    md = __build_instance()
    df = md.query_data(DataUtility.Selector('SSE'))
    print(df)
    df = md.query_data(DataUtility.Selector('SZSE'))
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










