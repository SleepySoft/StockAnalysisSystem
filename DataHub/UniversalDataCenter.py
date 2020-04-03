import sys
import datetime
import traceback
import pandas as pd

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Database import NoSqlRw
    from Database import UpdateTableEx
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
except Exception as e:
    sys.path.append(root_path)

    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Database import NoSqlRw
    from Database import UpdateTableEx
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
finally:
    logger = logging.getLogger('')


# UPDATE_STRATEGY_TYPE = int
#
# UPDATE_STRATEGY_AUTO = 1
# UPDATE_STRATEGY_POSITIVE = 2
# UPDATE_STRATEGY_MANUAL = 3
# UPDATE_STRATEGY_OFFLINE = 4


# ----------------------------------------------------------------------------------------------------------------------
#                                                 ParameterChecker
# ----------------------------------------------------------------------------------------------------------------------

class ParameterChecker:

    """
    Key: str - The key you need to check in the dict param
    Val: tuple - The first item: The list of expect types for this key, you can specify a None if None is allowed
                 The second item: The list of expect values for this key, an empty list means it can be any value
                 The third item: True if it's necessary, False if it's optional.
    DICT_PARAM_INFO_EXAMPLE = {
        'identity':     ([str], ['id1', 'id2'], True),
        'datetime':     ([datetime.datetime, None], [], False)
    }

    The param info for checking a dataframe.
    It's almost likely to the dict param info except the type should be str instead of real python type
    DATAFRAME_PARAM_INFO_EXAMPLE = {
        'identity':         (['str'], [], False),
        'period':           (['datetime'], [], True)
    }
    """

    PYTHON_DATAFRAME_TYPE_MAPPING = {
        'str': 'object',
        'list': 'object',
        'dict': 'object',
        'int': 'int64',
        'float': 'float64',
        'datetime': 'datetime64[ns]',
    }

    def __init__(self, df_param_info: dict = None, dict_param_info: dict = None):
        self.__df_param_info = df_param_info
        self.__dict_param_info = dict_param_info

    def check_dict(self, argv: dict) -> bool:
        if self.__dict_param_info is None or len(self.__dict_param_info) == 0:
            return True
        return ParameterChecker.check_dict_param(argv, self.__dict_param_info)

    def check_dataframe(self, df: dict) -> bool:
        if self.__df_param_info is None or len(self.__df_param_info) == 0:
            return True
        return ParameterChecker.check_dataframe_field(df, self.__df_param_info)

    @staticmethod
    def check_dict_param(argv: dict, param_info: dict) -> bool:
        if argv is None or len(argv) == 0:
            return False
        keys = list(argv.keys())

        for param in param_info.keys():
            types, values, must, _ = param_info[param]

            if param not in keys:
                if must:
                    logger.info('Param key check error: Param is missing - ' + param)
                    return False
                else:
                    continue

            value = argv[param]
            if value is None and None in types:
                continue
            if not isinstance(value, tuple([t for t in types if t is not None])):
                logger.info('Param key check error: Param type mismatch - ' +
                            str(type(value)) + ' is not in ' + str(types))
                return False

            if len(values) > 0:
                if value not in values:
                    logger.info('Param key check error: Param value out of range - ' +
                                str(value) + ' is not in ' + str(values))
                    return False
        return True

    @staticmethod
    def check_dataframe_field(df: pd.DataFrame, field_info: dict) -> bool:
        """
        Check whether DataFrame filed fits the field info.
        :param df: The DataFrame you want to check
        :param field_info: The definition of fields info
        :return: True if all fields are satisfied. False if not.
        """
        if df is None or len(df) == 0:
            return False
        columns = list(df.columns)

        for field in field_info.keys():
            types, values, must, _ = field_info[field]

            if field not in columns:
                if must:
                    logger.info('DataFrame field check error: Field is missing - ' + field)
                    return False
                else:
                    continue

            type_ok = False
            type_df = df[field].dtype
            for py_type in types:
                df_type = ParameterChecker.PYTHON_DATAFRAME_TYPE_MAPPING.get(py_type)
                if df_type is not None and df_type == type_df:
                    type_ok = True
                    break
            if not type_ok:
                logger.info('DataFrame field check error: Field type mismatch - ' +
                            field + ': ' + str(df_type) + ' not match ' + str(type_df))
                return False

            if len(values) > 0:
                out_of_range_values = df[~df[field].isin(values)]
                if len(out_of_range_values) > 0:
                    logger.info('DataFrame field check error: Field value out of range - ' +
                                str(out_of_range_values) + ' is not in ' + str(values))
                    return False
        return True


# ----------------------------------------------------------------------------------------------------------------------
#                                                 UniversalDataTable
# ----------------------------------------------------------------------------------------------------------------------

class UniversalDataTable:
    DEFAULT_SINCE_DATE = default_since()

    # -------------------------------- Base Separator --------------------------------

    class Extender:
        def __init__(self):
            pass
            # self.uri = ''
            # self.identity = ''
            # self.time_serial = ()
            # self.extra = {}
            # self.fields = []

        def parts(self, uri: str, identity: str or [str], time_serial: tuple, extra: dict, fields: list) -> \
                [(str, str or [str], tuple, dict, list)]:
            # self.uri = uri
            # self.identity = identity
            # self.time_serial = time_serial
            # self.extra = extra
            # self.fields = fields
            return [(uri, identity, time_serial, extra, fields)]

        def table_name(self, uri: str, identity: str, time_serial: tuple, extra: dict, fields: list) -> str:
            nop(self, identity, time_serial, extra, fields)
            return uri.replace('.', '_')

    # ------------------------------- UniversalDataTable -------------------------------

    def __init__(self,
                 uri: str, database_entry: DatabaseEntry,
                 depot_name: str, table_prefix: str = '',
                 identity_field: str or None = 'Identity',
                 datetime_field: str or None = 'DateTime',
                 extender: Extender = None):
        """
        If you specify both identity_field and datetime_field, the combination will be the primary key. Which means
            an id can have multiple different time serial record. e.g. stock daily price table.
        If you only specify the identity_field, the identity_field will be the only primary key. Which means
            its a time independent serial record with id. e.g. stock information table
        If you only specify the datetime_field, the datetime_field will be the only primary key. Which means
            it's a time serial record without id. e.g. log table
        If you do not specify neither identity_field and datetime_field, the table has not primary key. Which means
            the table cannot not updated by id or time. Record is increase only except update by manual.
        :param uri: The URI of the resource.
        :param database_entry: The instance of DatabaseEntry.
        :param depot_name: The name of database.
        :param table_prefix: The prefix of table, default empty.
        :param identity_field: The identity filed name.
        :param datetime_field: The datetime filed name.
        :param separator: The Separator to split data into parts.
        """
        self.__uri = uri
        self.__database_entry = database_entry
        self.__depot_name = depot_name
        self.__table_prefix = table_prefix
        self.__identity_field = identity_field
        self.__datetime_field = datetime_field
        self.__extender = extender if extender is not None else UniversalDataTable.Extender()

    def identity_field(self) -> str or None:
        return self.__identity_field

    def datetime_field(self) -> str or None:
        return self.__datetime_field

    # -------------------------------------------------------------------

    def adapt(self, uri: str) -> bool:
        return self.__uri.lower() == uri.lower()

    def query(self, uri: str, identity: str or [str], time_serial: tuple,
              extra: dict, fields: list) -> pd.DataFrame or None:
        on_column = []
        if str_available(self.__identity_field):
            on_column.append(self.__identity_field)
        if str_available(self.__datetime_field):
            on_column.append(self.__datetime_field)
        df_total = None
        for _uri, _identity, _time_serial, _extra, _fields in \
                self.__extender.parts(uri, identity, time_serial, extra, fields):
            table = self.data_table(_uri, _identity, _time_serial, _extra, fields)
            since, until = normalize_time_serial(_time_serial)
            result = table.query(_identity, since, until, _extra, _fields)
            df = pd.DataFrame(result)
            df_total = merge_on_columns(df_total, df, on_column)
        return df_total

    def merge(self, uri: str, identity: str, df: pd.DataFrame):
        table = self.data_table(uri, identity, (None, None), {}, [])
        identity_field, datetime_field = table.identity_field(), table.datetime_field()

        table.set_connection_threshold(1)
        for index, row in df.iterrows():
            identity_value = None
            if NoSqlRw.str_available(identity_field):
                if identity_field in list(row.index):
                    identity_value = row[identity_field]
            if NoSqlRw.str_available(identity_field) and identity_value is None:
                print('Warning: identity field "' + identity_field + '" of <' + uri + '> missing.')
                continue

            datetime_value = None
            if NoSqlRw.str_available(datetime_field):
                if datetime_field in list(row.index):
                    datetime_value = row[datetime_field]
                    if isinstance(datetime_value, str):
                        datetime_value = text_auto_time(datetime_value)
            if NoSqlRw.str_available(datetime_field) and datetime_value is None:
                print('Warning: datetime field "' + datetime_field + '" of <' + uri + '> missing.')
                continue
            table.bulk_upsert(identity_value, datetime_value, row.dropna().to_dict())
        table.bulk_flush()

    def range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        table = self.data_table(uri, identity, (None, None), {}, [])
        return (table.min_of(self.datetime_field(), identity), table.max_of(self.datetime_field(), identity)) \
            if str_available(self.datetime_field()) else (None, None)

    def ref_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        nop(self, uri, identity)
        return None, None

    def update_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        local_since, local_until = self.range(uri, identity)
        ref_since, ref_until = self.ref_range(uri, identity)
        return local_until, ref_until

    def data_table(self, uri: str, identity: str or [str],
                   time_serial: tuple, extra: dict, fields: list) -> NoSqlRw.ItkvTable:
        table_name = self.table_name(uri, identity, time_serial, extra, fields)
        return self.__database_entry.query_nosql_table(self.__depot_name, table_name,
                                                       self.__identity_field, self.__datetime_field)

    def table_name(self, uri: str, identity: str or [str], time_serial: tuple, extra: dict, fields: list) -> str:
        return self.__table_prefix + self.__extender.table_name(uri, identity, time_serial, extra, fields)


# ----------------------------------------------------------------------------------------------------------------------
#                                                UniversalDataCenter
# ----------------------------------------------------------------------------------------------------------------------

class UniversalDataCenter:
    def __init__(self, database_entry: DatabaseEntry, collector_plugin: PluginManager):
        self.__database_entry = database_entry
        self.__plugin_manager = collector_plugin
        self.__last_error = ''
        self.__data_table = []
        self.__field_uri_dict = {}
        self.__field_readable_dict = {}
        self.__readable_field_dict = {}

    def get_plugin_manager(self) -> PluginManager:
        return self.__plugin_manager

    def get_update_table(self) -> UpdateTableEx:
        return self.__database_entry.get_update_table()

    def get_data_table(self, uri: str) -> (UniversalDataTable, ParameterChecker):
        for table, checker in self.__data_table:
            if table.adapt(uri):
                return table, checker
        return None, None

    def get_last_error(self) -> str:
        return self.__last_error

    def log_error(self, error_text: str):
        self.__last_error = error_text

    def register_data_table(self, table: UniversalDataTable,
                            params_checker: ParameterChecker or None = None):
        if table not in self.__data_table:
            self.__data_table.append((table, params_checker))

    # ------------------------------------------------ Data Management -------------------------------------------------

    def query(self, uri: str, identity: str or [str] = None,
              time_serial: tuple = None, **extra) -> pd.DataFrame or None:
        return self.query_from_local(uri, identity, time_serial, extra)

    def query_from_local(self, uri: str, identity: str or [str] = None,
                         time_serial: tuple = None, extra: dict = None) -> pd.DataFrame or None:
        table, checker = self.get_data_table(uri)
        if table is None:
            self.log_error('Cannot find data table for : ' + uri)
            return None
        if not self.check_query_params(uri, identity, time_serial, **extra):
            return None
        if 'fields' in extra:
            fields = extra.get('fields')
            del extra['fields']
        else:
            fields = None
        if 'readable' in extra:
            readable = extra.get('readable')
            del extra['readable']
        else:
            readable = False

        if fields is not None and readable:
            fields = self.readable_to_fields(fields)

        result = table.query(uri, identity, time_serial, extra, fields)

        if fields is not None:
            # Fill the missing columns
            result = result.reindex(columns=fields)
            if readable:
                columns = list(result.columns)
                columns_mapping = self.field_map_readable(columns)
                result.rename(columns=columns_mapping, inplace=True)
        return result

    def query_from_plugin(self, uri: str, identity: str or [str] = None,
                          time_serial: tuple = None, **extra) -> pd.DataFrame or None:
        if not self.check_query_params(uri, identity, time_serial, **extra):
            return None
        argv = self.pack_query_params(uri, identity, time_serial, **extra)
        plugins = self.get_plugin_manager().find_module_has_capacity(uri)
        for plugin in plugins:
            result = self.get_plugin_manager().execute_module_function(plugin, 'query', argv)
            df = result[0] if len(result) > 0 else None
            if df is not None and isinstance(df, pd.DataFrame) and len(df) > 0:
                return df
        return None

    def update_local_data(self, uri: str, identity: str or [str] = None,
                          time_serial: tuple = None, force: bool = False, **extra) -> bool:
        return self.apply_local_data_patch(
            self.build_local_data_patch(uri, identity, time_serial, force, **extra))

    def build_local_data_patch(self, uri: str, identity: str or [str] = None,
                               time_serial: tuple = None, force: bool = False, **extra) -> tuple:
        """
        Calculate update range and fetch from plug-in, then pack for local persistence.
        """
        table, checker = self.get_data_table(uri)
        if table is None:
            self.log_error('Cannot find data table for : ' + uri)
            return False, (uri, identity, None, None, table), None

        # ---------------- Decide update time range ----------------
        if force:
            since, until = default_since(), now()
        else:
            since, until = self.calc_update_range(uri, identity, time_serial)
        # TODO: How to be more grace?
        if date2text(since) == date2text(until):
            # Does not need update.
            return True, (uri, identity, since, until, table), None
        print('%s: [%s] -> Update range: %s - %s' % (uri, str(identity), date2text(since), date2text(until)))

        # ------------------------- Fetch -------------------------
        result = self.query_from_plugin(uri, identity, (min(since, until), max(since, until)), **extra)
        if result is None or not isinstance(result, pd.DataFrame):
            self.log_error('Cannot fetch data from plugin for : ' + uri)
            return False, (uri, identity, since, until, table), result

        # ------------------------- Check -------------------------
        if checker is not None:
            if not checker.check_dataframe(result):
                self.log_error('Result format error: ' + uri)
                return False, (uri, identity, since, until, table), result
        return True, (uri, identity, since, until, table), result

    def apply_local_data_patch(self, patch: tuple) -> bool:
        """
        Merge and persistence the patch data.
        """
        # ------------------------- Unpack -------------------------
        try:
            ret, params, result = patch
            if not ret or result is None:
                return ret
            uri, identity, since, until, table = params
        except Exception as e:
            print(e)
            return False

        # ------------------------- Merge --------------------------

        clock = Clock()
        table.merge(uri, identity, result)
        print('%s: [%s] - Persistence finished, time spending: %sms' % (uri, str(identity), clock.elapsed_ms()))

        # ----------------------- Update Table ----------------------

        # Cache the update range in Update Table

        # 1.Update of uri
        update_tags = uri.split('.')
        self.get_update_table().update_latest_update_time(update_tags)
        self.get_update_table().update_update_range(update_tags, since, until)

        # 2.Update of each identity
        if str_available(identity):
            update_tags.append(identity.replace('.', '_'))
            self.get_update_table().update_latest_update_time(update_tags)
            self.get_update_table().update_update_range(update_tags, since, until)

        return True

    # ------------------------------------------------- Calc and Check -------------------------------------------------

    def calc_update_range(self, uri: str, identity: str or [str] = None,
                          time_serial: tuple = None) -> (datetime.datetime, datetime.datetime):
        table, _ = self.get_data_table(uri)
        if table is None:
            self.log_error('Cannot find data table for : ' + uri)
            return None, None

        update_tags = uri.split('.')
        if str_available(identity):
            update_tags.append(identity.replace('.', '_'))

        # ----------------- Decide update time range -----------------

        since, until = normalize_time_serial(time_serial, None, None)
        update_since, update_until = table.update_range(uri, identity)

        # Guess the update date time range
        # If the parameter user specified. Just use user specified.
        # If not, try to use the table update range to fill the missing one.
        # If table update range is not specified:
        #   - for since, use the default since date.
        #   - for until, use today.
        if since is None:
            if update_since is not None:
                since = update_since
            else:
                last_update = self.get_update_table().get_last_update_time(update_tags)
                since = last_update if last_update is not None else UniversalDataTable.DEFAULT_SINCE_DATE
        if until is None:
            if update_until is not None:
                until = update_until
            else:
                until = today()
        return since, until

    def pack_query_params(self, uri: str, identity: str or [str], time_serial: tuple, **extra) -> dict:
        table, _ = self.get_data_table(uri)

        if table is not None:
            identity_field = table.identity_field()
            datetime_field = table.datetime_field()
        else:
            identity_field = None
            datetime_field = None

        if not NoSqlRw.str_available(identity_field):
            identity_field = 'identity'
        if not NoSqlRw.str_available(datetime_field):
            datetime_field = 'datetime'

        pack = {'uri': uri}
        if extra is not None:
            pack.update(extra)
        if str_available(identity) and str_available(identity_field):
            pack[identity_field] = identity
        if time_serial is not None and str_available(datetime_field):
            pack[datetime_field] = time_serial
        return pack

    def check_query_params(self, uri: str, identity: str or [str], time_serial: tuple, **extra) -> bool:
        _, checker = self.get_data_table(uri)
        if checker is not None:
            argv = self.pack_query_params(uri, identity, time_serial, **extra)
            if not checker.check_dict(argv):
                self.log_error('Query format error: ' + uri)
                return False
        return True

    # ---------------------------------------------------- Readable ----------------------------------------------------

    # ----------------- Fields -----------------

    def fields_to_uri(self, fields: str):
        result = {}
        self.__check_cache_fields_declaration()
        for field in fields:
            uri = self.__field_uri_dict.get(field, 'None')
            if uri in result.keys():
                result[uri].append(field)
            else:
                result[uri] = [field]
        return result

    def check_fields_name(self, fields: [str]):
        self.__check_cache_fields_declaration()
        if not isinstance(fields, (tuple, list)):
            fields = [fields]
        for f in fields:
            if f not in self.__field_readable_dict.keys():
                return False
        return True

    def fields_to_readable(self, fields: [str]) -> [str]:
        self.__check_cache_fields_declaration()
        return [self.__field_readable_dict.get(f, f) for f in fields]

    def field_map_readable(self, fields: [str]) -> [str]:
        self.__check_cache_fields_declaration()
        return {f: self.__field_readable_dict.get(f, f) for f in fields}

    # ----------------- Readable -----------------

    def readable_to_uri(self, readable: str):
        result = {}
        self.__check_cache_fields_declaration()
        for r in readable:
            field = self.__readable_field_dict.get(r, '*')
            uri = self.__field_uri_dict.get(field, 'None')
            if uri in result.keys():
                result[uri].append(r)
            else:
                result[uri] = [r]
        return result

    def check_readable_name(self, readable: [str]):
        self.__check_cache_fields_declaration()
        if not isinstance(readable, (tuple, list)):
            readable = [readable]
        for r in readable:
            if r not in self.__readable_field_dict.keys():
                print('Unknown readable name: ' + r)
                return False
        return True

    def readable_to_fields(self, readable: [str]) -> [str]:
        self.__check_cache_fields_declaration()
        return [self.__readable_field_dict.get(r, r) for r in readable]

    def readable_map_field(self, readable: [str]) -> [str]:
        self.__check_cache_fields_declaration()
        return {r: self.__readable_field_dict.get(r, r) for r in readable}

    def __check_cache_fields_declaration(self):
        if len(self.__field_readable_dict) > 0 and len(self.__readable_field_dict) > 0:
            return
        field_probs = self.get_plugin_manager().execute_module_function(
            self.get_plugin_manager().all_modules(), 'fields', {}, False)
        for field_prob in field_probs:
            for uri, field_declare in field_prob.items():
                for field, readable in field_declare.items():
                    self.__field_uri_dict[field] = uri
                    self.__field_readable_dict[field] = readable
                    self.__readable_field_dict[readable] = field


# ----------------------------------------------------------------------------------------------------------------------
#                                                         Test
# ----------------------------------------------------------------------------------------------------------------------

def __build_data_center() -> UniversalDataCenter:
    plugin_path = root_path + '/Collector/'

    collector_plugin = PluginManager(plugin_path)
    collector_plugin.refresh()

    return UniversalDataCenter(DatabaseEntry(), collector_plugin)


def test_entry1():
    data_center = __build_data_center()
    df = data_center.query_from_plugin('test.entry1', 'identity_test1', ('2030-02-01', '2030-04-01'))
    print(df)
    assert len(df) == 28 + 30 + 1
    assert bool(set(list(df.columns)).intersection(['datetime', 'field_01', 'field_02', 'field_03', 'identity_test1']))


def test_update():
    data_center = __build_data_center()
    data_center.register_data_table(
        UniversalDataTable('test.entry1', DatabaseEntry(), 'test_db', 'test_table'))
    data_center.update_local_data('test.entry1', 'identity_test1')


def test_readable_to_fields():
    pass


def test_fields_to_readable():
    pass


def test_entry():
    # test_entry1()
    # test_update()
    test_readable_to_fields()


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

