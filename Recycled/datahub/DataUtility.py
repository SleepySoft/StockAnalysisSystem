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
    from Database import UpdateTableEx
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
except Exception as e:
    sys.path.append(root_path)

    from Utiltity.common import *
    from Utiltity.df_utility import *
    from Utiltity.time_utility import *
    from Database import UpdateTableEx
    from Database.DatabaseEntry import DatabaseEntry
    from Utiltity.plugin_manager import PluginManager
finally:
    logger = logging.getLogger('')


PYTHON_DATAFRAME_TYPE_MAPPING = {
    'str': 'object',
    'int64': 'int',
    'datetime': 'datetime64[ns]',
}


class Selector:
    def __init__(self, tags: [str],
                 since: datetime.datetime = None,
                 until: datetime.datetime = None,
                 extra: dict = None):
        self.tags = tags if isinstance(tags, list) else [tags]
        self.since = since
        self.until = until
        self.extra = extra

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return 'Selector(' + \
               str(self.tags) if self.tags is not None else 'None' + ', ' + \
               str(self.since) if self.since is not None else 'None' + ', ' + \
               str(self.until) if self.until is not None else 'None' + ', ' + \
               str(self.extra) if self.extra is not None else 'None' + ')'


Patch = Selector

RESULT_CODE = object
RESULT_FALSE = False
RESULT_TRUE = True
RESULT_SUCCESSFUL = 2
RESULT_FAILED = 4
RESULT_NOT_SUPPORTED = 8
RESULT_NOT_IMPLEMENTED = None

UPDATE_LAZY = 1
UPDATE_BATCH = 2
UPDATE_MANUAL = 3
UPDATE_OFFLINE = 4


class DataUtility:
    def __init__(self, plugin: PluginManager, update: UpdateTableEx):
        self.__plugin = plugin
        self.__update = update
        self.__update_strategy = UPDATE_LAZY

    def get_update_table(self) -> UpdateTableEx:
        return self.__update

    def get_plugin_manager(self) -> PluginManager:
        return self.__plugin

    def set_update_strategy(self, strategy: int):
        self.__update_strategy = strategy

    def get_update_strategy(self) -> int:
        return self.__update_strategy

    # --------------------------------------------------- public if ---------------------------------------------------

    def query_data(self, tags: [str] or Selector or [Selector],
                   since: datetime.datetime = None,
                   until: datetime.datetime = None,
                   extra: dict = None) -> pd.DataFrame or None:

        if isinstance(tags, (list, tuple)):
            if len(tags) > 0 and isinstance(tags[0], Selector):
                selectors = tags
            else:
                selectors = [Selector(tags, since, until, extra)]
        elif isinstance(tags, Selector):
            selectors = [tags]
        else:
            selectors = [Selector(tags, since, until, extra)]
        logger.info('DataUtility.query_data(' + str(selectors) + ')')

        sub_selectors = self.check_split_query(selectors)

        updated_patches = []
        patches = self.check_update_patch(sub_selectors)
        for patch in patches:
            result = self.execute_update_patch(patch)
            if result:
                updated_patches.append(patch)

        if len(updated_patches) > 0:
            self.trigger_save_data(updated_patches)

        result = None
        for selector in sub_selectors:
            df = self.data_from_cache(selector)
            if result is None:
                result = df
            else:
                result = concat_dataframe_by_row([result, df])
        return result

    def check_update_patch(self, selectors: [Selector]) -> [Patch]:
        """
        Check whether the tag specified data need update.
        Update strategy:
            0.ref_since is reserved
            1.latest update is None => Never been updated
                ->  Update all (patch_since = None, patch_until = None).
            2.ref_until is not None => Apply data range check
                -> If prev_until is None => Should be an error, update all (patch_since = None, patch_until = None).
                -> If prev_until less than ref_until => Update (since = tomorrow of previous until, until = ref_until)
                -> Else => Not need to update
            3.ref_until is None => Apply latest update check
                -> ref_latest_update is None => Should be an error, update all (patch_since = None, patch_until = None).
                -> latest_update < ref_until => Update (since = tomorrow of latest update, until = today)
                -> Else => Not need to update
        :param selectors: The selectors to identity the data
        :return: List of Patch.
        """
        logger.info('DataUtility.check_update(' + str(selectors) + ')')

        if self.__update_strategy == UPDATE_MANUAL:
            logger.info('  | MANUAL - Return False')
            return RESULT_FALSE
        if self.__update_strategy == UPDATE_OFFLINE:
            logger.info('  | OFFLINE - Return False')
            return RESULT_FALSE

        update_patches = []
        for selector in selectors:
            patch = self._check_single_selector_patch(selector)
            if patch is not None:
                update_patches.append(patch)
        return update_patches

    def check_split_query(self, selectors: Selector or [Selector]) -> [Selector]:
        nop(self)
        return [selectors] if isinstance(selectors, Selector) else selectors

    # --------------------------------------------------- private if ---------------------------------------------------

    def execute_update_patch(self, patch: Patch) -> RESULT_CODE:
        nop(self)
        logger.info('DataUtility.execute_update_patch(' + str(patch) + ') -> RESULT_NOT_IMPLEMENTED')
        return RESULT_NOT_IMPLEMENTED

    def trigger_save_data(self, patches: [Patch]) -> RESULT_CODE:
        nop(self)
        logger.info('DataUtility.trigger_save_data(' + str(patches) + ') -> RESULT_NOT_IMPLEMENTED')

    def data_from_cache(self, selector: Selector) -> pd.DataFrame or None:
        logger.info('DataUtility.data_from_cache(' + str(selector) + ') -> RESULT_NOT_IMPLEMENTED')
        return RESULT_NOT_IMPLEMENTED

    # -------------------------------------------------- probability --------------------------------------------------

    def get_root_tags(self) -> [str]:
        nop(self)
        return []

    def is_data_support(self, tags: [str]) -> bool:
        nop(self, tags)
        return False

    def get_cached_data_range(self, tags: [str]) -> (datetime.datetime, datetime.datetime):
        _tags = self.__normalize_tags(tags)
        return self.get_update_table().get_since_until(*_tags)

    def get_cache_last_update(self, tags: [str]) -> datetime.datetime:
        _tags = self.__normalize_tags(tags)
        return self.get_update_table().update_latest_update_time(*_tags)

    def get_reference_data_range(self, tags: [str]) -> (datetime.datetime, datetime.datetime):
        nop(self, tags)
        return [None, yesterday()]

    def get_reference_last_update(self, tags: [str]) -> datetime.datetime:
        nop(self, tags)
        return today()

    # ---------------------------------------------------- private -----------------------------------------------------

    def _check_single_selector_patch(self, selector: Selector) -> Patch or None:
        latest_update = self._get_data_last_update(selector.tags)
        if latest_update is None:
            return Patch(selector.tags, None, None, selector.extra)

        ref_since, ref_until = self.get_reference_data_range(selector.tags)
        if ref_until is not None:
            since, until = self.get_cached_data_range(selector.tags)
            if until is None:
                logger.error('DataUtility.check_update: until is None. Update all.')
                return Patch(selector.tags, None, None, selector.extra)
            elif until < ref_until:
                return Patch(selector.tags, tomorrow_of(until), ref_until, selector.extra)
            else:
                logger.info('DataUtility.check_update: Check data range - Not need update.')
                return None
        else:
            ref_latest_update = self.get_reference_last_update(selector.tags)
            if ref_latest_update is None:
                logger.error('DataUtility.check_update: ref_latest_update is None. Update all.')
                return Patch(selector.tags, None, None, selector.extra)
            elif latest_update < ref_latest_update:
                return Patch(selector.tags, tomorrow_of(latest_update), ref_latest_update, selector.extra)
            else:
                logger.info('DataUtility.check_update: Check latest update - Not need update.')
                return []

    # --------------------------------------------------- assistance ---------------------------------------------------

    def _get_data_range(self, tags: list) -> (datetime.datetime, datetime.datetime):
        return self.__update.get_since_until(tags)

    def _get_data_last_update(self, tags: list) -> datetime.datetime:
        return self.__update.get_last_update_time(tags)

    # def _cache_data_satisfied(self, tags: list, since: datetime.datetime, until: datetime.datetime) -> bool:
    #     _tags = self.__normalize_tags(tags)
    #     _since, _until = self._get_data_range(_tags)
    #     return since >= _since and until <= _until

    def _update_time_record(self, tags: [str], df: pd.DataFrame, time_field: str):
        if len(df) == 0:
            return
        _tags = self.__normalize_tags(tags)
        min_date = min(df[time_field])
        max_date = max(df[time_field])
        if min_date is not None:
            self.get_update_table().update_since(_tags, min_date)
        if max_date is not None:
            self.get_update_table().update_until(_tags, max_date)
        self.get_update_table().update_latest_update_time(_tags)

    # def _check_update_by_range(self, tags: [str]) -> (RESULT_CODE, datetime, datetime):
    #     ref_since, ref_until = self.get_reference_data_range(tags)
    #     if ref_since is None and ref_until is None:
    #         return DataUtility.RESULT_NOT_SUPPORTED, None, None
    #
    #     need_update = DataUtility.RESULT_FALSE
    #     update_since, update_until = None, None
    #     since, until = self.get_cached_data_range(tags)
    #
    #     if ref_since is not None:
    #         if since is None or since > ref_since:
    #             update_since = ref_since
    #             need_update = DataUtility.RESULT_TRUE
    #     if ref_until is not None:
    #         if until is None or until < ref_until:
    #             update_until = ref_until
    #             need_update = DataUtility.RESULT_TRUE
    #
    #     if update_since is None and until is not None:
    #         update_since = tomorrow_of(until)
    #     if update_until is None and since is not None:
    #         update_until = yesterday_of(since)
    #
    #     if update_since is not None and update_until is not None and update_since >= update_until:
    #         need_update = DataUtility.RESULT_FALSE
    #     return need_update, update_since, update_until
    #
    # def _check_update_by_last_update(self, tags: [str]) -> (RESULT_CODE, datetime, datetime):
    #     reference_last_update = self.get_reference_last_update(tags)
    #     if reference_last_update is None:
    #         return DataUtility.RESULT_NOT_SUPPORTED, None, None
    #     else:
    #         last_update = self._get_data_last_update(tags)
    #         if last_update is None or last_update < today():
    #             need_update = DataUtility.RESULT_TRUE
    #         else:
    #             need_update = DataUtility.RESULT_FALSE
    #         return need_update, None, None

    def _check_dict_param(self, argv: dict, param_info: dict, must_params: list = None) -> bool:
        nop(self)
        if argv is None or len(argv) == 0:
            return False
        keys = list(argv.keys())
        for param in param_info.keys():
            if param not in keys:
                if must_params is None or param in must_params:
                    logger.info('Param key check error: Param is missing - ' + param)
                    return False
                else:
                    continue

            value = argv[param]
            types, values = param_info[param]
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

    def _check_dataframe_field(self, df: pd.DataFrame, field_info: dict, must_fields: list = None) -> bool:
        """
        Check whether DataFrame filed fits the field info.
        :param df: The DataFrame you want to check
        :param field_info: The definition of fields info
        :param must_fields: The must fields.
                            If not None, the specified fields must exist.
                            If None, all fields should exist.
        :return: True if all fields are satisfied. False if not.
        """
        nop(self)
        if df is None or len(df) == 0:
            return False
        columns = list(df.columns)
        for field in field_info.keys():
            if field not in columns:
                if must_fields is None or field in must_fields:
                    logger.info('DataFrame field check error: Field is missing - ' + field)
                    return False
                else:
                    continue

            type_ok = False
            type_df = df[field].dtype
            types, values = field_info[field]
            for py_type in types:
                df_type = PYTHON_DATAFRAME_TYPE_MAPPING.get(py_type)
                if df_type is not None and df_type == type_df:
                    type_ok = True
                    break
            if not type_ok:
                logger.info('DataFrame field check error: Field type mismatch - ' +
                            str(df_type) + ' is not in ' + str(df_type))
                return False

            if len(values) > 0:
                out_of_range_values = df[~df[field].isin(values)]
                if len(out_of_range_values) > 0:
                    logger.info('DataFrame field check error: Field value out of range - ' +
                                str(out_of_range_values) + ' is not in ' + str(values))
                    return False
        return True

    def __normalize_tags(self, tags: list) -> list:
        nop(self)
        return tags if isinstance(tags, list) else [tags]
