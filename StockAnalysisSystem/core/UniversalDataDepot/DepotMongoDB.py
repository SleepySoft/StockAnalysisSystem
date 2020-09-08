import time
import traceback

import numpy as np
import pandas as pd
from bson import Code
from pymongo import MongoClient, ASCENDING, UpdateOne, InsertOne       # UpdateMany, DeleteOne, DeleteMany
from .DepotInterface import DepotInterface


# ----------------------------------------------------------------------------------------------------------------------
#                                                      DepotMongoDB
# ----------------------------------------------------------------------------------------------------------------------

class DepotMongoDB(DepotInterface):
    def __init__(self, primary_keys: [str], client: MongoClient, database: str, data_table: str):
        super(DepotMongoDB, self).__init__(primary_keys)

        self.__client = client
        self.__database = database
        self.__data_table = data_table

        self.__connection_count = 0
        self.__connection_threshold = 100

    # ------------------------------- Basic Operation -------------------------------

    def query(self, *args, conditions: dict = None, fields: [str] or None = None, **kwargs) -> pd.DataFrame or None:
        collection = self.__get_collection()
        if collection is None:
            return None

        spec = self.__gen_find_spec(*args, conditions=conditions)
        select_fields = None if fields is None else {f: 1 for f in fields}

        result = collection.find(spec, select_fields)
        df = pd.DataFrame(list(result))

        return df

    def insert(self, dataset: pd.DataFrame or dict or any) -> bool:
        return self.__xsert(dataset, 0)

    def upsert(self, dataset: pd.DataFrame or dict or any) -> bool:
        return self.__xsert(dataset, 1)

    def delete(self, *args, conditions: dict = None, fields: [str] or None = None,
               delete_all: bool = False, **kwargs) -> bool:
        collection = self.__get_collection()
        if collection is None:
            return False

        spec = self.__gen_find_spec(*args, conditions=conditions)
        if len(spec) == 0 and not delete_all:
            self.log('Warning: No condition for delete. '
                     'If you want to delete all documents. '
                     'Please specify delete_all=True')
            return False

        if fields is None:
            result = collection.delete_many(spec)
        else:
            del_keys = {}
            for key in fields:
                del_keys[key] = 1
            result = collection.update(spec, {'$unset': del_keys}, False, True, True)

        # TODO: Parse result

        return True

    def drop(self) -> bool:
        collection = self.__get_collection()
        if collection is None:
            return False
        collection.drop()
        return True

    def range_of(self, field: str, *args, conditions: dict = None, **kwargs) -> (any, any):
        collection = self.__get_collection()
        if collection is None:
            return None, None

        spec = self.__gen_find_spec(*args, conditions=conditions)
        result = collection.aggregate([
            {'$match': spec},
            {'$group': {
                '_id': None,
                'max': {'$max': '$' + field},
                'min': {'$min': '$' + field}
            }}
        ])
        result_l = list(result)
        return (None, None) if len(result_l) == 0 else (result_l[0]['min'], result_l[0]['max'])

    def record_count(self) -> int:
        collection = self.__get_collection()
        return collection.estimated_document_count() if collection is not None else 0

    def distinct_value_of_field(self, field: str) -> [str]:
        collection = self.__get_collection()
        return [] if collection is None else collection.distinct(field)

    def all_fields(self) -> [str]:
        """
        Get all the keys from the collection.
        Keys is unique. Exclude '_id'.
        :return: The list of keys
        """
        collection = self.__get_collection()
        if collection is None:
            return []
        _map = Code('function() { for (var key in this) { emit(key, null); } }')
        _reduce = Code('function(key, stuff) { return null; }')
        result = collection.map_reduce(_map, _reduce, 'results')
        keys = result.distinct('_id')
        keys.remove('_id')
        return keys

    def remove_field(self, key: str) -> bool:
        collection = self.__get_collection()
        if collection is None:
            return False
        return collection.update_many(
            {key: {'$exists': True}},  # criteria
            {'$unset': {key: 1}},  # modifier
            False  # no need to upsert
        )

    def rename_field(self, field_old: str, field_new: str) -> bool:
        collection = self.__get_collection()
        if collection is None:
            return False
        return collection.update_many(
            {},  # criteria
            {'$rename': {field_old: field_new}},  # modifier
            False  # no need to upsert
        )

    # ---------------------------------------------------------------------

    def __get_collection(self):
        if self.__client is None:
            return None
        self.__check_recycle_connection()
        db = self.__client[self.__database]
        if db is None:
            return None
        if not self.__collection_exists(db, self.__data_table):
            collection = db[self.__data_table]
            self.__check_create_index(collection)
        else:
            collection = db[self.__data_table]
        self.__connection_count += 1
        return collection

    def __check_create_index(self, collection):
        index = [(k, ASCENDING) for k in self.primary_keys()]
        if len(index) > 0:
            collection.create_index(index, unique=True)

    def __check_recycle_connection(self):
        if self.__connection_count >= self.__connection_threshold:
            # Close the previous connections. Avoiding resource and memory leak.
            # https://api.mongodb.com/python/current/api/pymongo/mongo_client.html#pymongo.mongo_client.MongoClient.close
            #   Close all sockets in the connection pools and stop the monitor threads. If this instance is used
            #   again it will be automatically re-opened and the threads restarted unless auto encryption is enabled.
            self.__client.close()
            self.__connection_count = 0

    def __xsert(self, dataset: pd.DataFrame or dict or any, operation: int) -> bool:
        # 0: Insert
        # 1: Upsert

        ret, data_dict = self.__process_xsert_prarm(dataset)
        if not ret:
            return False

        collection = self.__get_collection()
        if collection is None:
            return False

        bulk_operations = []
        for document in data_dict:
            # Consider "array like" value
            clean_doc = {k: v for k, v in document.items() if not (pd.notnull(v) is False)}
            if operation == 0:
                bulk_operations.append(InsertOne({'$set': clean_doc}))
            elif operation == 1:
                spec = self.__gen_upsert_spec(document)
                bulk_operations.append(UpdateOne(spec, {'$set': clean_doc}, upsert=True))
            else:
                assert False
            # Max 1000 operations
            try:
                if len(bulk_operations) >= 1000:
                    collection.bulk_write(bulk_operations)
                    bulk_operations.clear()
            except Exception as e:
                print('Error update: ' + str(e))
                print(traceback.format_exc())
            finally:
                pass
        if len(bulk_operations) > 0:
            collection.bulk_write(bulk_operations)
            bulk_operations.clear()
        return True

    def __process_xsert_prarm(self, dataset: pd.DataFrame or dict or any) -> (bool, [dict]):
        if not self.check_primary_keys(dataset):
            return False, None
        if isinstance(dataset, pd.DataFrame):
            # s1 = time.time()
            # data_dict = dataset.T.apply(lambda x: x.dropna().to_dict()).tolist()
            # print('Method1 - Timespending: %sms' % int((time.time() - s1) * 1000))
            #
            # s2 = time.time()
            data_dict = dataset.to_dict('records')
            # print('Method2 - Timespending: %sms' % int((time.time() - s2) * 1000))
            # data_dict = _data.T.to_dict().values()
            # print('Convert DataFrame size(%d) time spending: %s' % (len(_data), clock.elapsed_s()))
        elif isinstance(dataset, dict):
            data_dict = [dataset]
        elif isinstance(dataset, (list, tuple)):
            data_dict = dataset
        else:
            return False, None
        return True, data_dict

    def __gen_find_spec(self, *args, conditions: dict) -> dict:
        full_conditions = self.full_conditions(*args, conditions=conditions)
        spec = {}
        for k, v in full_conditions.items():
            if isinstance(v, tuple):
                # Range
                sub_cond = {}
                if len(v) >= 1 and v[0] is not None:
                    sub_cond['$gte'] = v[0]
                if len(v) >= 2 and v[1] is not None:
                    sub_cond['$lte'] = v[1]
                if len(sub_cond) > 0:
                    spec[k] = sub_cond
                else:
                    self.log('Warning: Range condition %s invalid. Ignore.' % k)
            elif isinstance(v, list):
                # In list
                spec[k] = {'$in': v}
            else:
                # Equal
                spec[k] = {'$eq': v}
        return spec

    def __gen_upsert_spec(self, document: dict):
        spec = {}
        for primary_key in self.primary_keys():
            if primary_key in document.keys():
                spec[primary_key] = document[primary_key]
                del document[primary_key]
        return spec

    @staticmethod
    def __collection_exists(db, collection_name: str) -> bool:
        return collection_name in db.list_collection_names()

    @staticmethod
    def __collection_empty(db, collection_name: str) -> bool:
        return not DepotMongoDB.__collection_exists(db, collection_name) or\
               (db[collection_name].count == 0)
