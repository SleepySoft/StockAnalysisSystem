import json
import sys
import traceback
from bson import Code
from datetime import datetime
from pymongo import MongoClient, ASCENDING, UpdateOne, UpdateMany, InsertOne, DeleteOne, DeleteMany


# ---------------------- Duplicate Functions: Because we don't want this file depends other files ----------------------

def str_available(value: str) -> bool:
    return value is not None and isinstance(value, str) and value != ''


def text2date(text: str) -> datetime:
    return datetime.strptime(text, '%Y-%m-%d')


def text2datetime(text: str) -> datetime:
    return datetime.strptime(text, '%Y-%m-%d %H:%M:%S')


def text_auto_time(text: str) -> datetime:
    if isinstance(text, datetime):
        return text
    # noinspection PyBroadException
    try:
        return datetime.strptime(text, '%Y-%m-%d')
    except Exception:
        pass
    # noinspection PyBroadException
    try:
        return datetime.strptime(text, '%H:%M:%S')
    except Exception:
        pass
    # noinspection PyBroadException
    try:
        return datetime.strptime(text, '%Y-%m-%d %H:%M:%S')
    except Exception:
        pass
    return None


def date2text(time: datetime) -> str:
    return time.strftime('%Y-%m-%d')


def datetime2text(time: datetime) -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S')


# ----------------------------------------------------------------------------------------------------------------------
#                                                     ItkvTable
# Identity & Time, Key-Value Table
#
# ----------------------------------------------------------------------------------------------------------------------

class ItkvTable:
    """ A table which can easily extend its column, with identity and time as its main key.
    Itkv = Identity, DateTime, Key, Value
    This table is based on NoSQL (MongoDB)
    It must contain an Identity and a Timestamp as unique index
    Other Key-Value pairs are extendable
    """

    def __init__(self, client: MongoClient, database: str, table: str,
                 identity_field: str = 'Identity', datetime_field: str = 'DateTime'):
        self.__client = client
        self.__database = database
        self.__table = table
        self.__connection_count = -1
        self.__connection_threshold = 100
        self.__identity_field = identity_field
        self.__datetime_field = datetime_field
        self.__bulk_operations = []
        self.__key_unique = True

    def identity_field(self) -> str or None:
        return self.__identity_field

    def datetime_field(self) -> str or None:
        return self.__datetime_field

    def set_key_uniqueness(self, unique: bool):
        self.__key_unique = unique

    def set_connection_threshold(self, threshold: int):
        self.__connection_threshold = threshold
        self.__check_recycle_connection()

    # -----------------------------------------------------------------

    def drop(self):
        collection = self.__get_collection()
        if collection is None:
            return
        collection.drop()

    def import_json(self, json_str: str) -> bool:
        try:
            json_data = json.loads(json_str)
            collection = self.__get_collection()
            collection.drop()
            collection.insert_many(json_data)
            return True
        except Exception as e:
            print('Import json for collection [%s] fail: ' % self.__table)
            print(e)
            return False
        finally:
            pass

    def count(self) -> int:
        collection = self.__get_collection()
        if collection is None:
            return 0
        return collection.count()

    # ------------------------------------------------ Bulk Operations -------------------------------------------------

    def bulk_upsert(self, identity: str, time: datetime or str, data: dict, extra_spec: dict = None):
        spec, document = self.__gen_upsert_spec_and_document(identity, time, data, extra_spec)
        self.__bulk_operations.append(UpdateOne(spec, {'$set': document}, upsert=True))
        if len(self.__bulk_operations) > 950:
            self.bulk_flush()

    def bulk_flush(self) -> dict or None:
        collection = self.__get_collection()
        if collection is None:
            while len(self.__bulk_operations) > 1000:
                self.__bulk_operations.pop(0)
            return None
        try:
            ret = collection.bulk_write(self.__bulk_operations)
            self.__bulk_operations.clear()
        except Exception as e:
            ret = None
            print('ItkvTable.bulk_flush() fail: ')
            print(e)
        finally:
            self.__client.close()
        return ret

    # ----------------------------------------------- Single Operations ------------------------------------------------

    def upsert(self, identity: str, time: datetime or str, data: dict, extra_spec: dict = None) -> dict or None:
        """ Update a record, insert if not exists.
        Args:
            identity    : str or list of str, None if you don't want to specify
            time        : datetime or time format str, None if you don't want to specify
            data        : the data that you want to update or insert
            extra_spec  : dict, to specify the extra conditions, None if you don't want to specify
            identity and time are also the conditions to find the entries
        Return value:
            The result of API returns, as dict
        Raises:
            None
        """
        collection = self.__get_collection()
        if collection is None:
            return None
        spec, document = self.__gen_upsert_spec_and_document(identity, time, data, extra_spec)
        try:
            ret = collection.update_many(spec, {'$set': document}, True) \
                if len(spec) > 0 else collection.insert(document)
        except Exception as e:
            ret = None
        finally:
            pass
        return ret

    def delete(self, identity: str or list = None, since: datetime = None, until: datetime = None,
               extra_spec: dict = None, keys: list = None):
        """ Delete document or delete key-value in document.
        Args:
            identity        : str or list of str, None if you don't want to specify
            since           : datetime or time format str, None if you don't want to specify
            until           : datetime or time format str, None if you don't want to specify
            extra_spec      : dict, to specify the extra conditions, None if you don't want to specify
            keys            : The keys you want to remove, None to move the whole document
        Return value:
            The result of API returns, as dict
        Raises:
            None
        """

        collection = self.__get_collection()
        if collection is None:
            return False
        spec = self.__gen_find_spec(identity, since, until, extra_spec)

        if keys is None:
            return collection.delete_many(spec)
        else:
            del_keys = {}
            for key in keys:
                del_keys[key] = 1
            return collection.update(spec, {'$unset': del_keys}, False, True, True)

    # Query records
    # keys - The keys you want to list in your query, None to list all
    def query(self, identity: str or list = None, since: datetime = None, until: datetime = None,
              extra_spec: dict = None, keys: list = None) -> list:
        """ Query records
        Args:
            identity        : str or list of str, None if you don't want to specify
            since, until    : datetime or time format str, None if you don't want to specify
            extra_spec      : dict, to specify the extra conditions, None if you don't want to specify
            keys            : The keys you want to query, None to query all entries
        Return value:
            Result as dict list
        Raises:
            None
        """

        collection = self.__get_collection()
        if collection is None:
            return []
        spec = self.__gen_find_spec(identity, since, until, extra_spec)

        key_select = None
        if keys is not None:
            key_select = {}
            for key in keys:
                key_select[key] = 1
        result = collection.find(spec, key_select)
        return list(result)

    def min_of(self, field: str, identity: str = None) -> any:
        collection = self.__get_collection()
        if collection is None:
            return None
        spec = self.__gen_find_spec(identity)
        spec[field] = {'$exists': True}
        result = list(collection.find(spec).sort([(field, +1)]).limit(1))
        return result[0].get(field, None) if result is not None and len(result) > 0 else None

    def max_of(self, field: str, identity: str = None) -> any:
        collection = self.__get_collection()
        if collection is None:
            return None
        spec = self.__gen_find_spec(identity)
        spec[field] = {'$exists': True}
        result = list(collection.find(spec).sort([(field, -1)]).limit(1))
        return result[0].get(field, None) if result is not None and len(result) > 0 else None

    def get_all_keys(self):
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

    def get_distinct_values(self, field: str) -> [str]:
        collection = self.__get_collection()
        return collection.distinct(field)

    def remove_key(self, key: str) -> bool:
        collection = self.__get_collection()
        if collection is None:
            return False
        return collection.update_many(
            {key: {'$exists': True}},   # criteria
            {'$unset': {key: 1}},       # modifier
            False                       # no need to upsert
        )

    def replace_key(self, key_old: str, key_new: str) -> bool:
        collection = self.__get_collection()
        if collection is None:
            return False
        return collection.update_many(
            {},   # criteria
            {'$rename': {key_old: key_new}},     # modifier
            False                               # no need to upsert
        )

    # ------------------------------------------------------------------------------------------------------------------

    def __get_collection(self):
        if self.__client is None:
            return None
        self.__check_recycle_connection()
        db = self.__client[self.__database]
        if db is None:
            return None
        collection = db[self.__table]
        if self.__connection_count == -1:
            self.__check_create_index(collection)
            self.__connection_count = 0
        self.__connection_count += 1
        return collection

    def __check_create_index(self, collection):
        index = []
        if str_available(self.__identity_field):
            index.append((self.__identity_field, ASCENDING))
        if str_available(self.__datetime_field):
            index.append((self.__datetime_field, ASCENDING))
        collection.create_index(index, background=True)

    def __check_recycle_connection(self):
        if self.__connection_count >= self.__connection_threshold:
            # Close the previous connections. Avoiding resource and memory leak.
            # https://api.mongodb.com/python/current/api/pymongo/mongo_client.html#pymongo.mongo_client.MongoClient.close
            #   Close all sockets in the connection pools and stop the monitor threads. If this instance is used
            #   again it will be automatically re-opened and the threads restarted unless auto encryption is enabled.
            self.__client.close()
            self.__connection_count = 0

    def __gen_find_spec(self, identity: str or list,
                        since: datetime or str = None,
                        until: datetime or str = None,
                        extra_spec: dict = None) -> dict:
        """ Generate find spec for NoSQL query.
        Args:
            identity        : str or list of str, None if you don't want to specify
            since, until    : datetime or time format str, None if you don't want to specify
            extra_spec      : dict, to specify the extra conditions, None if you don't want to specify
        Return value:
            The spec dict
        Raises:
            None
        """

        spec = {}
        if str_available(self.__identity_field):
            if str_available(identity):
                spec = {self.__identity_field: identity}
            elif isinstance(identity, (list, tuple)):
                spec = {self.__identity_field: {'$in': list(identity)}}

        if isinstance(since, str):
            since = text_auto_time(since)
        elif isinstance(since, datetime) or since is None:
            pass
        # else:
        #     raise Exception('<since> should be time format str or datetime, or just None')

        if isinstance(until, str):
            until = text_auto_time(until)
        elif isinstance(until, datetime) or until is None:
            pass
        # else:
            # raise Exception('<until> should be time format str or datetime, or just None')

        time_limit = {}
        if since is not None or until is not None:
            if since == until:
                time_limit['$eq'] = until
            else:
                if since is not None:
                    time_limit['$gte'] = since
                if until is not None:
                    time_limit['$lte'] = until
        if str_available(self.__datetime_field) and len(time_limit) > 0:
            spec[self.__datetime_field] = time_limit

        if extra_spec is not None and len(extra_spec) > 0:
            spec.update(extra_spec)

        return spec

    def __gen_upsert_spec_and_document(self, identity: str, time: datetime or str,
                                       data: dict, extra_spec: dict = None) -> (dict, dict):
        if self.__key_unique:
            spec = self.__gen_find_spec(identity, time, time, extra_spec)
        else:
            spec = {}
        if isinstance(time, str):
            time = text_auto_time(time)
        document = {}
        if str_available(self.__identity_field) and str_available(identity):
            document[self.__identity_field] = identity
        if str_available(self.__datetime_field) and time is not None:
            document[self.__datetime_field] = time
        document.update(data)
        return spec, document


# ----------------------------------------------------- Test Code ------------------------------------------------------

def __prepare_empty_test_table() -> ItkvTable:
    client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5)
    assert(client is not None)

    table = ItkvTable(client, 'TestDatabase', 'TestTable')
    table.drop()

    return table


def __prepare_default_test_data() -> ItkvTable:
    table = __prepare_empty_test_table()
    table.upsert('identity1', '2000-05-01', {
        'PI': 3.1415926,
        'Speed of Light': 299792458,
        'Password': "Who's your daddy",
        "Schindler's List": ['Trump', 'Bili', 'Anonymous'],
        'Author': 'Sleepy',
    })
    table.upsert('identity2', '2020-03-01', {
        'A1': 111,
        'B1': 222,
        'C1': 333,
        "D1": 444,
        'Author': 'Sleepy',
    })
    return table


def test_basic_update_query_drop():
    table = __prepare_default_test_data()

    result = table.query('identity1')
    assert(len(result) == 1)
    document = result[0]
    assert(document['PI'] == 3.1415926)
    assert(document['Speed of Light'] == 299792458)
    assert(document['Password'] == "Who's your daddy")
    assert(document["Schindler's List"] == ['Trump', 'Bili', 'Anonymous'])

    table.drop()

    result = table.query('identity1')
    assert(len(result) == 0)


def test_query():
    table = __prepare_default_test_data()

    # Test since option

    result = table.query(since='2010-01-01')
    assert(len(result) == 1)

    result = table.query(since='2020-03-01')
    assert(len(result) == 1)

    result = table.query(since='2020-03-01 00:00:01')
    assert(len(result) == 0)

    result = table.query(since='2000-05-01')
    assert(len(result) == 2)

    # Test until option

    result = table.query(until='2010-01-01')
    assert(len(result) == 1)

    result = table.query(until='2000-05-01')
    assert(len(result) == 1)

    result = table.query(until='2000-04-30 23:59:29')
    assert(len(result) == 0)

    result = table.query(until='2030-01-01')
    assert(len(result) == 2)

    # Test extra_spec

    result = table.query(extra_spec={'A1': 111})
    assert(len(result) == 1)

    result = table.query(extra_spec={'PI': 3.14})
    assert(len(result) == 0)

    result = table.query(extra_spec={'Author': 'Sleepy'})
    assert(len(result) == 2)


def test_delete_document():
    table = __prepare_default_test_data()
    assert(len(table.query()) == 2)
    table.delete('identity1')
    assert(len(table.query()) == 1)

    table = __prepare_default_test_data()
    assert(len(table.query()) == 2)
    table.delete(since='2015-01-01')
    assert(len(table.query()) == 1)

    table = __prepare_default_test_data()
    assert(len(table.query()) == 2)
    table.delete(since='2000-01-01')
    assert(len(table.query()) == 0)

    table = __prepare_default_test_data()
    assert(len(table.query()) == 2)
    table.delete(until='2019-09-01')
    assert(len(table.query()) == 1)

    table = __prepare_default_test_data()
    assert(len(table.query()) == 2)
    table.delete(until='2020-09-01')
    assert(len(table.query()) == 0)

    table = __prepare_default_test_data()
    assert(len(table.query()) == 2)
    table.delete(extra_spec={'A1': 111})
    assert(len(table.query()) == 1)

    table = __prepare_default_test_data()
    assert(len(table.query()) == 2)
    table.delete(extra_spec={'Author': 'Sleepy'})
    assert(len(table.query()) == 0)


def test_delete_key_value():
    table = __prepare_default_test_data()
    assert(len(table.query()) == 2)

    table.delete(keys=['PI', 'A1', 'Author'])
    collection = table.query()

    assert(len(collection) == 2)
    for document in collection:
        assert('PI' not in document.keys())
        assert('A1' not in document.keys())
        assert('Author' not in document.keys())


def test_update_key_value():
    table = __prepare_default_test_data()
    assert(len(table.query()) == 2)

    table.upsert('identity1', data={
        'PI': 3.14,
        'Password': "Greed is good",
        'New': 'New Item',
    })

    table.upsert('identity3', '2015-06-06', data={
        'D1': 555,
        'Password': "Greed is good",
        'New': 'New Item',
    })

    table.upsert('identity1', '2000-05-01', {
        'PI': 3.1415926,
        'Speed of Light': 299792458,
        'Password': "Who's your daddy",
        "Schindler's List": ['Trump', 'Bili', 'Anonymous'],
        'Author': 'Sleepy',
    })
    table.upsert('identity2', '2020-03-01', {
        'A1': 111,
        'B1': 222,
        'C1': 333,
        "D1": 444,
        'Author': 'Sleepy',
    })


def test_get_all_keys():
    table = __prepare_default_test_data()
    table.upsert('identity3', '2020-04-01', {
        'A1': 111,
        'B1': 222,
        'C1': 333,
        "D1": 444,
        'Author2': 'Sleepy',
    })
    result = table.get_all_keys()
    print(result)
    assert(result == ['A1', 'Author', 'Author2', 'B1', 'C1', 'D1', 'DateTime', 'Identity', 'PI',
                      'Password', "Schindler's List", 'Speed of Light'])


def test_remove_key():
    table = __prepare_default_test_data()
    table.upsert('identity3', '2020-04-01', {
        'A1': 111,
        'B1': 222,
        'C1': 333,
        "D1": 444,
        'Author2': 'Sleepy',
    })
    result = table.get_all_keys()
    print(result)
    assert(result == ['A1', 'Author', 'Author2', 'B1', 'C1', 'D1', 'DateTime', 'Identity', 'PI',
                      'Password', "Schindler's List", 'Speed of Light'])

    table.remove_key('A1')
    table.remove_key('B1')
    table.remove_key('Author')
    result = table.get_all_keys()
    print(result)
    assert(result == ['Author2', 'C1', 'D1', 'DateTime', 'Identity', 'PI',
                      'Password', "Schindler's List", 'Speed of Light'])


def test_min_max():
    table = __prepare_empty_test_table()

    table.upsert('identity1', '1990-12-31', {'Foo': 'bar1'})
    table.upsert('identity2', '1990-01-01', {'Foo': 'bar2'})
    table.upsert('identity3', '2000-05-10', {'Foo': 'bar3'})
    table.upsert('identity4', '2000-02-28', {'Foo': 'bar4'})
    table.upsert('identity5', '2100-11-11', {'Foo': 'bar5'})
    table.upsert('identity6', '2100-02-02', {'Foo': 'bar6'})
    table.upsert('identity7', '2200-12-01', {'Foo': 'bar7'})
    table.upsert('identity8', '2200-01-01', {'Foo': 'bar8'})
    table.upsert('identity9', '',           {'Foo': 'bar9'})

    min_time = table.min_of('DateTime')
    max_time = table.max_of('DateTime')

    assert str(min_time) == '1990-01-01 00:00:00'
    assert str(max_time) == '2200-12-01 00:00:00'


def test_upsert_by_identity_and_datetime():
    table = __prepare_empty_test_table()

    print('------------------------------- upsert_by_identity_and_datetime 01 -------------------------------')

    table.upsert('identity1', '2000-01-01', {'Foo1': 'bar1'})
    table.upsert('identity2', '2000-02-01', {'Foo2': 'bar2'})
    table.upsert('identity3', '2000-03-01', {'Foo3': 'bar3'})
    table.upsert('identity4', '2000-04-01', {'Foo4': 'bar4'})
    table.upsert('identity5', '2000-04-01', {'Foo5': 'bar5'})

    result = table.query()
    print(result)
    assert(len(result) == 5)

    print('------------------------------- upsert_by_identity_and_datetime 02 -------------------------------')

    table.upsert('identity1', '2000-01-01', {'Foo1': 'bar1', 'Foo2': 'bar2'})
    table.upsert('identity1', '2000-02-01', {'Foo1': 'bar1', 'Foo2': 'bar2'})
    table.upsert('identity1', '2000-03-01', {'Foo1': 'bar1', 'Foo2': 'bar2'})

    result = table.query('identity1')
    print(result)
    assert(len(result) == 3)


def test_upsert_by_identity_or_datetime():
    table = __prepare_empty_test_table()

    print('------------------------------- upsert_by_identity_or_datetime 00 -------------------------------')

    table.upsert('identity1', '', {'Foo1': 'bar1'})
    table.upsert('identity2', None, {'Foo2': 'bar2'})
    table.upsert(None, None, {'Foo3': 'bar3'})
    table.upsert('', '2000-04-01', {'Foo4': 'bar4'})
    table.upsert(None, '2000-05-01', {'Foo5': 'bar5'})

    result = table.query()
    print(result)
    assert(len(result) == 5)

    print('------------------------------- upsert_by_identity_or_datetime 03 -------------------------------')

    # Without identity and time, just insert anyway

    table.upsert('', None, {'Foo1': 'bar1'})
    table.upsert(None, '', {'Foo2': 'bar2'})
    table.upsert(None, None, {'Foo3': 'bar3'})

    result = table.query()
    print(result)
    assert(len(result) == 8)

    print('------------------------------- upsert_by_identity_or_datetime 01 -------------------------------')

    table.upsert('identity1', '', {'Foo2': 'bar2'})
    table.upsert('identity1', None, {'Foo3': 'bar3'})

    result = table.query('identity1')
    print(result)
    assert(len(result) == 1)
    assert(result[0]['Foo1'] == 'bar1')
    assert(result[0]['Foo2'] == 'bar2')
    assert(result[0]['Foo3'] == 'bar3')

    print('------------------------------- upsert_by_identity_or_datetime 02 -------------------------------')

    table.upsert('identity2', None, {'Foo1': 'bar1'})
    table.upsert('identity2', '', {'Foo2': 'bar2'})
    table.upsert('identity2', None, {'Foo3': 'bar3'})

    result = table.query('identity2')
    print(result)
    assert(len(result) == 1)
    assert(result[0]['Foo1'] == 'bar1')
    assert(result[0]['Foo2'] == 'bar2')
    assert(result[0]['Foo3'] == 'bar3')

    print('------------------------------- upsert_by_identity_or_datetime 0405 -------------------------------')

    table.upsert('', '2000-04-01', {'Foo4': 'bar44'})
    table.upsert('', '2000-04-01', {'Foo7': 'bar7'})
    table.upsert(None, '2000-04-01', {'Foo6': 'bar6'})
    table.upsert(None, '2000-05-01', {'Foo9': 'bar9'})

    result = table.query(None, '2000-04-01', '2000-04-01')
    print(result)
    assert(len(result) == 1)
    assert(result[0]['Foo4'] == 'bar44')
    assert(result[0]['Foo7'] == 'bar7')
    assert(result[0]['Foo6'] == 'bar6')

    result = table.query('', '2000-05-01', '2000-05-01')
    print(result)
    assert(len(result) == 1)
    assert(result[0]['Foo5'] == 'bar5')
    assert(result[0]['Foo9'] == 'bar9')


def test_entry():
    test_basic_update_query_drop()
    test_query()
    test_delete_document()
    test_delete_key_value()
    test_get_all_keys()
    test_remove_key()
    test_min_max()
    test_upsert_by_identity_and_datetime()
    test_upsert_by_identity_or_datetime()


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


# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------- DEPRECATED -----------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
#                                                     UniversalTable
#
# ----------------------------------------------------------------------------------------------------------------------

# class UniversalTable:
#     def __init__(self, client: MongoClient, database: str, table: str):
#         self.__client = client
#         self.__database = database
#         self.__table = table
#
#     def drop(self):
#         collection = self.__get_collection()
#         if collection is None:
#             return True
#         collection.drop()
#
#     def count(self) -> int:
#         collection = self.__get_collection()
#         if collection is None:
#             return 0
#         return collection.count()
#
#     def upsert(self, in_spec: dict, range_spec: dict, data: dict, extra_spec: dict = None) -> dict:
#         """ Update a record, insert if not exists.
#         Args:
#             identity    : str or list of str, None if you don't want to specify
#             time        : datetime or time format str, None if you don't want to specify
#             extra_spec  : dict, to specify the extra conditions, None if you don't want to specify
#             identity and time are also the conditions to find the entries
#         Return value:
#             The result of API returns, as dict
#         Raises:
#             None
#         """
#
#         collection = self.__get_collection()
#         if collection is None:
#             return False
#         spec = self.__gen_find_spec(identity, time, time, extra_spec)
#         if isinstance(time, str):
#             time = text_auto_time(time)
#         document = {
#             'Identity': identity,
#             'DateTime': datetime2text(time),
#             **data
#         }
#         return collection.update_many(spec, {'$set': document}, True)
#
#     def delete(self, identity: str or list = None, since: datetime = None, until: datetime = None,
#                extra_spec: dict = None, keys: list = None):
#         """ Delete document or delete key-value in document.
#         Args:
#             identity        : str or list of str, None if you don't want to specify
#             since, until    : datetime or time format str, None if you don't want to specify
#             extra_spec      : dict, to specify the extra conditions, None if you don't want to specify
#             keys            : The keys you want to remove, None to move the whole document
#         Return value:
#             The result of API returns, as dict
#         Raises:
#             None
#         """
#
#         collection = self.__get_collection()
#         if collection is None:
#             return False
#         spec = self.__gen_find_spec(identity, since, until, extra_spec)
#
#         if keys is None:
#             return collection.delete_many(spec)
#         else:
#             del_keys = {}
#             for key in keys:
#                 del_keys[key] = 1
#             return collection.update(spec, {'$unset': del_keys}, False, True, True)
#
#     # Query records
#     # keys - The keys you want to list in your query, None to list all
#     def query(self, identity: str or list = None, since: datetime = None, until: datetime = None,
#               extra_spec: dict = None, keys: list = None) -> list:
#         """ Query records
#         Args:
#             identity        : str or list of str, None if you don't want to specify
#             since, until    : datetime or time format str, None if you don't want to specify
#             extra_spec      : dict, to specify the extra conditions, None if you don't want to specify
#             keys            : The keys you want to query, None to query all entries
#         Return value:
#             Result as dict list
#         Raises:
#             None
#         """
#
#         collection = self.__get_collection()
#         if collection is None:
#             return []
#         spec = self.__gen_find_spec(identity, since, until, extra_spec)
#
#         key_select = None
#         if keys is not None:
#             key_select = {}
#             for key in keys:
#                 key_select[key] = 1
#         result = collection.find(spec, key_select)
#         return list(result)
#
#     def get_all_keys(self):
#         """
#         Get all the keys from the collection.
#         Keys is unique. Exclude '_id'.
#         :return: The list of keys
#         """
#         collection = self.__get_collection()
#         if collection is None:
#             return []
#         _map = Code('function() { for (var key in this) { emit(key, null); } }')
#         _reduce = Code('function(key, stuff) { return null; }')
#         result = collection.map_reduce(_map, _reduce, 'results')
#         keys = result.distinct('_id')
#         keys.remove('_id')
#         return keys
#
#     def remove_key(self, key: str) -> bool:
#         collection = self.__get_collection()
#         if collection is None:
#             return False
#         return collection.update_many(
#             {key: {'$exists': True}},   # criteria
#             {'$unset': {key: 1}},       # modifier
#             False                       # no need to upsert
#         )
#
#   # ------------------------------------------------------------------------------------------------------------------
#
#     def __get_collection(self):
#         if self.__client is None:
#             return None
#         db = self.__client[self.__database]
#         if db is None:
#             return None
#         collection = db[self.__table]
#         return collection
#
#     def __gen_find_spec(self, in_spec: dict, range_spec: dict, extra_spec: dict = None) -> dict:
#         """ Generate find spec for NoSQL query.
#         Args:
#             identity        : str or list of str, None if you don't want to specify
#             since, until    : datetime or time format str, None if you don't want to specify
#             extra_spec      : dict, to specify the extra conditions, None if you don't want to specify
#         Return value:
#             The spec dict
#         Raises:
#             None
#         """
#
#         spec = {}
#         if isinstance(in_spec, dict):
#             for key in in_spec.keys():
#                 value = in_spec[key]
#         elif isinstance(identity, str):
#             spec = {'Identity': identity}
#         elif isinstance(identity, list):
#             spec = {'Identity': {'$in': identity}}
#         else:
#             raise Exception('<identity> should be str or a list of str, or just None')
#
#         if isinstance(since, str):
#             since = text_auto_time(since)
#         elif isinstance(since, datetime) or since is None:
#             pass
#         else:
#             raise Exception('<since> should be time format str or datetime, or just None')
#
#         if isinstance(until, str):
#             until = text_auto_time(until)
#         elif isinstance(until, datetime) or until is None:
#             pass
#         else:
#             raise Exception('<until> should be time format str or datetime, or just None')
#
#         time_limit = {}
#         if since is not None:
#             time_limit['$gte'] = datetime2text(since)
#         if until is not None:
#             time_limit['$lte'] = datetime2text(until)
#         if len(time_limit) > 0:
#             spec['DateTime'] = time_limit
#
#         if extra_spec is not None and len(extra_spec) > 0:
#             spec.update(extra_spec)
#
#         return spec
#
#     def __parse_in_spec(self, in_spec: dict) -> dict:
#         """
#         Example: {
#             key1: key1 value as str,
#             key2: key2 values as list or tuple,
#         }
#         :param in_spec: The "in spec"
#         :return: Parsed spec in dict
#         """
#         spec = {}
#         for key in in_spec.keys():
#             value = in_spec[key]
#             if isinstance(key, str):
#                 spec[key] = value
#             elif isinstance(key, (list, tuple)):
#                 spec[key] = {'$in': list(value)}
#             else:
#                 print('Incorrect type of value in "in spec" : ' + 'key' + '(' + str(type(value)) + ')')
#         return spec
#
#     def __parse_range_spec(self, range_spec: str) -> dict:
#         """
#         Example: {
#             key1: ('gt', key1_greater_than_value),
#             key2: ('ge', key2_greater_eq_value),
#             key1: ('lt', key1_less_than_value),
#             key2: ('le', key2_less_eq_value),
#         }
#         :param range_spec:
#         :return:
#         """
#         spec = {}
#         for key in range_spec.keys():
#             value = in_spec[key]
#             if isinstance(key, str):
#                 spec[key] = value
#             elif isinstance(key, list):
#                 spec[key] = {'$in': value}
#             else:
#                 print('Incorrect type of value in "in spec" : ' + 'key' + '(' + str(type(value)) + ')')
#         return spec


