from .DataAgent import *
from ..Utiltity.common import *
from ..Utiltity.df_utility import *
from ..Utiltity.time_utility import *
from ..Database import NoSqlRw
from ..Database import UpdateTableEx
from ..Database.DatabaseEntry import DatabaseEntry
from ..Utiltity.plugin_manager import PluginManager


# ----------------------------------------------------------------------------------------------------------------------
#                                                UniversalDataCenter
# ----------------------------------------------------------------------------------------------------------------------

class UniversalDataCenter:
    def __init__(self, database_entry: DatabaseEntry, collector_plugin: PluginManager):
        self.__database_entry = database_entry
        self.__plugin_manager = collector_plugin

        # self.__data_source = []
        self.__factor_center = None

        self.__last_error = ''
        self.__data_agent = []
        self.__field_uri_dict = {}
        self.__field_readable_dict = {}
        self.__readable_field_dict = {}

    def get_plugin_manager(self) -> PluginManager:
        return self.__plugin_manager

    def get_update_table(self) -> UpdateTableEx:
        return self.__database_entry.get_update_table()

    def get_all_uri(self):
        return [agent.base_uri() for agent in self.__data_agent]

    def get_all_agents(self) -> [DataAgent]:
        return self.__data_agent

    def get_data_agent(self, uri: str) -> DataAgent or None:
        for agent in self.__data_agent:
            if agent.adapt(uri):
                return agent
        return None

    def get_last_error(self) -> str:
        return self.__last_error

    def log_error(self, error_text: str):
        self.__last_error = error_text

    # def add_data_source(self, source):
    #     self.__data_source.append(source)

    def set_factor_center(self, factor_center):
        self.__factor_center = factor_center

    def register_data_agent(self, agent: DataAgent):
        if agent not in self.__data_agent:
            self.__data_agent.append(agent)

    # ------------------------------------------------ Data Management -------------------------------------------------

    def query(self, uri: str, identity: str or [str] = None,
              time_serial: tuple = None, **extra) -> pd.DataFrame or None:
        result = self.query_from_local(uri, identity, time_serial, extra)
        # TODO: It's not a good way. Some problem need to be resolved.
        # 1.The field not exists at all
        # 2.Query multiple fields, some of them not persist on local
        # if result is None or len(result) == 0:
        #     result = self.query_from_plugin(uri, identity, time_serial, **extra)
        return result

    def query_from_local(self, uri: str, identity: str or [str] = None,
                         time_serial: tuple = None, extra: dict = None) -> pd.DataFrame or None:
        extra_param = extra.copy()
        agent = self.get_data_agent(uri)
        
        if agent is None:
            self.log_error('Cannot find data table for : ' + uri)
            return None
        if not self.check_query_params(uri, identity, time_serial, **extra_param):
            return None
        if 'fields' in extra_param:
            fields = extra_param.get('fields')
            del extra_param['fields']
        else:
            fields = None
        if 'readable' in extra_param:
            readable = extra_param.get('readable')
            del extra_param['readable']
        else:
            readable = False

        if fields is not None and readable:
            fields = self.readable_to_fields(fields)

        result = agent.query(uri, identity, time_serial, extra_param, fields)

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
        extra_param = extra.copy()
        if not self.check_query_params(uri, identity, time_serial, **extra_param):
            return None
        if 'Factor' in uri:
            return self.query_from_factor(uri, identity, time_serial, **extra_param)
        else:
            return self.query_from_collector(uri, identity, time_serial, **extra_param)

    def query_from_factor(self, uri: str, identity: str or [str] = None,
                          time_serial: tuple = None, **extra) -> pd.DataFrame or None:
        if self.__factor_center is None:
            return None
        factor = extra.get('fields', [])
        mapping = extra.get('mapping', {})
        return self.__factor_center.query(identity, factor, time_serial, mapping, extra)

    def query_from_collector(self, uri: str, identity: str or [str] = None,
                             time_serial: tuple = None, **extra) -> pd.DataFrame or None:
        argv = self.pack_query_params(uri, identity, time_serial, **extra)
        plugins = self.get_plugin_manager().find_module_has_capacity(uri)
        for plugin in plugins:
            result = self.get_plugin_manager().execute_module_function(plugin, 'query', argv)
            df = result[0] if len(result) > 0 else None
            if df is not None and isinstance(df, pd.DataFrame) and len(df) > 0:
                return df
        return None

    # -----------------------------------------------------------------------------------------

    def update_local_data(self, uri: str, identity: str or [str] = None,
                          time_serial: tuple = None, force: bool = False, **extra) -> bool:
        return self.apply_local_data_patch(
            self.build_local_data_patch(uri, identity, time_serial, force, **extra))

    def build_local_data_patch(self, uri: str, identity: str or [str] = None,
                               time_serial: tuple = None, force: bool = False, **extra) -> tuple:
        """
        Calculate update range and fetch from plug-in, then pack for local persistence.
        """
        agent = self.get_data_agent(uri)
        checker = agent.get_field_checker() if agent is not None else None

        if agent is None:
            self.log_error('Cannot find data table for : ' + uri)
            return False, (uri, identity, None, None, agent), None

        # ---------------- Decide update time range ----------------
        if force:
            since, until = default_since(), now()
        else:
            since, until = self.calc_update_range(uri, identity, time_serial)
        # TODO: How to be more grace?
        if date2text(since) == date2text(until):
            # Does not need update.
            return True, (uri, identity, since, until, agent), None
        print('%s: [%s] -> Update range: %s - %s' % (uri, str(identity), date2text(since), date2text(until)))

        # ------------------------- Fetch -------------------------
        result = self.query_from_plugin(uri, identity, (min(since, until), max(since, until)), **extra)
        if result is None or not isinstance(result, pd.DataFrame):
            self.log_error('Cannot fetch data from plugin for : ' + uri)
            return False, (uri, identity, since, until, agent), result

        # ------------------------- Check -------------------------
        if checker is not None:
            if not checker.check_dataframe(result):
                self.log_error('Result format error: ' + uri)
                return False, (uri, identity, since, until, agent), result
        return True, (uri, identity, since, until, agent), result

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
        agent = self.get_data_agent(uri)
        if agent is None:
            self.log_error('Cannot find data table for : ' + uri)
            return None, None

        update_tags = uri.split('.')
        if str_available(identity):
            update_tags.append(identity.replace('.', '_'))

        # ----------------- Decide update time range -----------------

        since, until = normalize_time_serial(time_serial, None, None)
        update_since, update_until = agent.update_range(uri, identity)

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
                since = last_update if last_update is not None else DataAgentUtility.a_share_market_start()
        if until is None:
            if update_until is not None:
                until = update_until
            else:
                until = today()
        return since, until

    def pack_query_params(self, uri: str, identity: str or [str], time_serial: tuple, **extra) -> dict:
        agent = self.get_data_agent(uri)

        if agent is not None:
            identity_field = agent.identity_field()
            datetime_field = agent.datetime_field()
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
        agent = self.get_data_agent(uri)
        checker = agent.get_field_checker() if agent is not None else None

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








