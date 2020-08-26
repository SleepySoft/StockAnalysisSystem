import os

import h5py
import numpy as np
import pandas as pd
from .DepotInterface import DepotInterface


def pad_with(vector, pad_width, iaxis, kwargs):
    pad_value = kwargs.get('padder', '')
    vector[:pad_width[0]] = pad_value
    vector[-pad_width[1]:] = pad_value
    return vector


# ----------------------------------------------------------------------------------------------------------------------
#                                                      DepotMongoDB
# ----------------------------------------------------------------------------------------------------------------------

class DepotHDF5(DepotInterface):
    def __init__(self, primary_keys: [str], file_path: str, compress: bool = False):
        super(DepotHDF5, self).__init__(primary_keys)
        self.__file_path = file_path
        self.__compress = compress

        if len(primary_keys) > 2:
            self.log('Warning: DepotHDF5 only support 2 primary keys.')

    # ------------------------------- Basic Operation -------------------------------

    def query(self, *args, conditions: dict = None, fields: [str] or None = None, **kwargs) -> pd.DataFrame or None:
        try:
            f = h5py.File(self.file_path(), 'r')
        except Exception as e:
            self.log('Open file %s for read fail.' % self.file_path())
            return None
        finally:
            pass

        full_conditions = self.full_conditions(*args, conditions=conditions)
        result = self.__query_dispatch(f, full_conditions, 0)

        return result

    def insert(self, dataset: pd.DataFrame or dict or any) -> bool:
        pass

    def upsert(self, dataset: pd.DataFrame or dict or any) -> bool:
        if not self.check_primary_keys(dataset):
            return False
        if not isinstance(dataset, pd.DataFrame):
            self.log('DepotHDF5.upsert() only supports DataFrame')
            return False
        try:
            f = h5py.File(self.file_path(), 'a')
        except Exception as e:
            self.log('Open file % for append fail, create instead.' % self.file_path())
            f = h5py.File(self.file_path(), 'w')
        finally:
            pass
        self.__write_dispatch(f, dataset, 0)
        return True

    def delete(self, *args, conditions: dict = None, fields: [str] or None = None,
               delete_all: bool = False, **kwargs) -> bool:
        pass

    def drop(self):
        try:
            if os.path.exists(self.file_path()):
                os.remove(self.file_path())
        except Exception as e:
            self.log('Drop file %s fail.' % self.file_path())
        finally:
            pass

    # ----------------------------- Advanced Operation ------------------------------

    def range_of(self, field, *args, conditions: dict = None, **kwargs) -> (any, any):
        primary_keys = self.primary_keys()
        full_conditions = self.full_conditions(*args, conditions=conditions)

        if len(primary_keys) >= 2 and primary_keys[0] not in full_conditions.keys():
            self.log('Error: To get hdf5 depot data range. You should specify the level-1 group: ' + primary_keys[0])
            return (None, None)

        try:
            f = h5py.File(self.file_path(), 'r')
        except Exception as e:
            self.log('Open file %s for read fail.' % self.file_path())
            return None
        finally:
            pass

    def record_count(self) -> int:
        pass

    def distinct_value_of_field(self, field: str) -> [str]:
        pass

    def all_fields(self) -> [str]:
        pass

    def remove_field(self, key: str) -> bool:
        pass

    def rename_field(self, field_old: str, field_new: str) -> bool:
        pass

    # ----------------------------------------------------------------------------------

    def file_path(self) -> str:
        return self.__file_path

    def __write_dispatch(self, current_group: h5py.Group, df: pd.DataFrame, group_level: int):
        # Currently only the first primary key will be the group
        if group_level == 0 and len(self.primary_keys()) > 1:
            self.__write_process_group(current_group, df, group_level)
        else:
            self.__write_process_dataset(current_group, df, group_level)

    def __write_process_group(self, current_group: h5py.Group, df: pd.DataFrame, group_level: int):
        primary_keys = self.primary_keys()
        group_field = primary_keys[group_level]
        df_group = df.groupby(group_field)
        for g, d in df_group:
            next_group = current_group[g] if g in current_group.keys() else current_group.create_group(g)
            self.__write_dispatch(next_group, d.drop(group_field, axis=1), group_level + 1)

    def __write_process_dataset(self, current_group: h5py.Group, df: pd.DataFrame, dataset_level: int):
        primary_keys = self.primary_keys()
        primary_key_fields = primary_keys[dataset_level:]

        # Make every column in the same length
        padding_dataset, max_len = self.__check_fill_dataset_group_alignment(current_group)

        if len(primary_key_fields) == 0 or max_len == 0:
            # Just insert
            insert_df = df
        else:
            update_df = df.dropna(subset=primary_key_fields)
            exists_df = self.__dataset_group_to_dataframe(current_group)
            upsert_df = pd.concat([exists_df, update_df], axis=0)
            upsert_df = upsert_df.drop_duplicates(primary_key_fields, keep='last')

            # upsert_df = exists_df.reindex(columns=update_df.columns | exists_df.columns)
            # upsert_df.update(update_df)
            # upsert_df = exists_df.merge(update_df, on=primary_key_fields, how='outer', indicator=True)
            # Remove all old data and re-insert
            self.__delete_all_dataset_in_group(current_group)
            max_len = 0
            insert_df = upsert_df

        for column in insert_df.columns:
            s = insert_df[column]
            np_arr = s.to_numpy()
            if column not in current_group.keys():
                # https://stackoverflow.com/a/40312924/12929244
                if np_arr.dtype.kind == 'O':
                    if max_len > 0:
                        np_arr = np.pad(np_arr, (max_len, 0), pad_with)
                    string_dt = h5py.special_dtype(vlen=str)
                    current_group.create_dataset(column, data=np_arr, dtype=string_dt,
                                                 maxshape=(None,), chunks=True)
                else:
                    if max_len > 0:
                        np_arr = np.pad(np_arr, (max_len, 0))
                    current_group.create_dataset(column, data=np_arr,
                                                 maxshape=(None,), chunks=True)
                print('Create dataset %s, length = %s' % (column, np_arr.shape[0]))
            else:
                append_len = np_arr.shape[0]
                exists_len = current_group[column].shape[0]
                current_group[column].resize((exists_len + append_len, ))
                current_group[column][-append_len:] = np_arr
                print('Append dataset %s, length %s -> %s' % (column, exists_len, (exists_len + append_len)))

    def __query_dispatch(self, current_group: h5py.Group, conditions: dict, pk_level: int) -> pd.DataFrame:
        # Currently only the first primary key will be the group
        if pk_level == 0 and len(self.primary_keys()) > 1:
            return self.__query_process_group(current_group, conditions, pk_level)
        else:
            return self.__query_process_dataset(current_group, conditions)

    def __query_process_group(self, current_group: h5py.Group, conditions: dict, pk_level: int) -> pd.DataFrame:
        pk = self.primary_keys()[pk_level]
        if pk in conditions:
            cond = conditions[pk]
            if isinstance(cond, list):
                select_groups = [k for k in current_group.keys() if k in cond]
            elif isinstance(cond, tuple):
                select_groups = [k for k in current_group.keys() if self.judge_range_condition(k, cond)]
            elif isinstance(cond, str):
                select_groups = [pk] if pk in current_group.keys() else []
            else:
                select_groups = []
                self.log('Warning: HDF5 Depot not support condition: ' + str(cond))
        else:
            select_groups = current_group.keys()

        result = None
        for key in select_groups:
            df = self.__query_dispatch(current_group[key], conditions, pk_level + 1)
            if df is None or df.empty:
                continue

            # Assign the column of group
            df[pk] = key

            if result is None:
                result = df
            else:
                result = pd.concat([result, df], axis=0)

        return result

    def __query_process_dataset(self, current_group: h5py.Group, conditions: dict) -> pd.DataFrame:
        result = self.__dataset_group_to_dataframe(current_group)
        if result is None or result.empty:
            return result
        for k in conditions.keys():
            if k not in result.columns:
                self.log('Warning: Field %s not in result.' % k)
                continue
            cond = conditions[k]
            if isinstance(cond, list):
                result = result[result[k] in cond]
            elif isinstance(cond, tuple):
                def cond_wrapper(field: str, range_cond: tuple):
                    return lambda x: self.judge_range_condition(x[field], range_cond)
                result = result[result.apply(cond_wrapper(k, cond), axis=1, reduce=True)]
            elif isinstance(cond, str):
                result = result[result[k] == cond]
            else:
                self.log('Warning: HDF5 Depot not support condition: ' + str(cond))
        return result

    def __dataset_group_to_dataframe(self, group: h5py.Group) -> pd.DataFrame:
        padding_dataset, max_len = self.__check_fill_dataset_group_alignment(group)
        if len(padding_dataset) != 0:
            self.log('Warning: Padding data to fields of h5py group: ' + str(padding_dataset))

        df = pd.DataFrame()
        for column in group.keys():
            np_arr = group[column]
            df[column] = np_arr
        return df

    def __delete_all_dataset_in_group(self, group: h5py.Group):
        keys = group.keys()
        for k in keys:
            del group[k]

    def __check_fill_dataset_group_alignment(self, group: h5py.Group) -> ([str], int):
        max_len = 0
        padding_dataset = []
        for key in group.keys():
            dataset: h5py.Dataset = group[key]
            max_len = max(max_len, dataset.shape[0])
        for key in group.keys():
            dataset: h5py.Dataset = group[key]
            ds_len = dataset.shape[0]
            if ds_len < max_len:
                padding_dataset.append(key)
                dataset.resize((max_len, ))
        return padding_dataset, max_len






