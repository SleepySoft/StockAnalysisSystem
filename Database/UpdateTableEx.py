import traceback
from pymongo import MongoClient

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Database.NoSqlRw import *
    from Utiltity.time_utility import *
except Exception as e:
    sys.path.append(root_path)

    from Database.NoSqlRw import *
    from Utiltity.time_utility import *
finally:
    pass


class UpdateTableEx:
    def __init__(self, client: MongoClient, database: str = 'StockAnalysisSystem', table: str = 'UpdateTable'):
        self.__table = ItkvTable(client, database, table, 'tags', 'last_update')

    # ------------------------------------ Gets ------------------------------------

    def get_since(self, tags: [str]):
        record = self.__table.query(self.__normalize_tags(tags), keys=['since'])
        return record[0].get('since') if record is not None and len(record) > 0 else None

    def get_until(self, tags: [str]):
        record = self.__table.query(self.__normalize_tags(tags), keys=['until'])
        return record[0].get('until') if record is not None and len(record) > 0 else None

    def get_since_until(self, tags: [str]):
        record = self.__table.query(self.__normalize_tags(tags), keys=['since', 'until'])
        return record[0].get('since') if record is not None and len(record) > 0 else None, \
               record[0].get('until') if record is not None and len(record) > 0 else None

    def get_last_update_time(self, tags: [str]):
        record = self.__table.query(self.__normalize_tags(tags), keys=['last_update'])
        return record[0].get('last_update') if record is not None and len(record) > 0 else None

    def get_all_time(self, tags: [str]):
        record = self.__table.query(self.__normalize_tags(tags), keys=['since', 'until', 'last_update'])
        return record[0].get('since') if record is not None and len(record) > 0 else None, \
               record[0].get('until') if record is not None and len(record) > 0 else None, \
               record[0].get('last_update') if record is not None and len(record) > 0 else None

    def get_update_record(self, tags: [str]):
        return self.__table.query(self.__normalize_tags(tags))

    # ----------------------------------- Updates -----------------------------------

    def update_since(self, tags: [str], since: datetime or str) -> bool:
        if since is None:
            return False
        since = text_auto_time(since)
        old_since = self.get_since(tags)
        if old_since is None or since < old_since:
            print('Update since: ' + str(tags) + ' -> ' + str(since))
            self.__table.upsert(self.__normalize_tags(tags), None, data={'since': since})
        return True

    def update_until(self, tags: [str], until: datetime or str) -> bool:
        if until is None:
            return False
        until = text_auto_time(until)
        old_until = self.get_until(tags)
        if old_until is None or until > old_until:
            print('Update until: ' + str(tags) + ' -> ' + str(until))
            self.__table.upsert(self.__normalize_tags(tags), None, data={'until': until})
        return True

    def update_update_range(self, tags: [str], since: datetime or str, until: datetime or str) -> bool:
        ret1 = self.update_since(tags, since)
        ret2 = self.update_until(tags, until)
        return ret1 and ret2

    def update_latest_update_time(self, tags: [str]) -> bool:
        print('Update latest update time: ' + str(tags) + ' -> ' + str(now()))
        self.__table.upsert(self.__normalize_tags(tags), None, data={'last_update': now()})
        return True

    def delete_update_record(self, tags: [str]) -> bool:
        self.__table.delete(self.__normalize_tags(tags))
        return True

    def clear_update_records(self) -> bool:
        self.__table.drop()
        return True

    # ------------------------------------------------------------------------------------------------------------------

    def __normalize_tags(self, tags: [str]) -> str:
        return ('.'.join(tags)).replace(' ', '') if isinstance(tags, (list, tuple)) else str(tags).strip()

    # TABLE = 'UpdateTableEx'
    # FIELD = ['serial', 'tags', 'since', 'until', 'latest_update']
    # INDEX_SINCE = 2
    # INDEX_UNTIL = 3
    # INDEX_LAST_UPDATE = 4
    #
    # def __init__(self, sql_db: SqlAccess):
    #     self.__sql_db = sql_db
    #
    # def get_since(self, tags: [str]):
    #     record = self.get_update_record(tags)
    #     return None if len(record) == 0 else text_auto_time(record[0][UpdateTableEx.INDEX_SINCE])
    #
    # def get_until(self, tags: [str]):
    #     record = self.get_update_record(tags)
    #     return None if len(record) == 0 else text_auto_time(record[0][UpdateTableEx.INDEX_UNTIL])
    #
    # def get_since_until(self, tags: [str]):
    #     record = self.get_update_record(tags)
    #     return None if len(record) == 0 else text_auto_time(record[0][UpdateTableEx.INDEX_SINCE]), \
    #            None if len(record) == 0 else text_auto_time(record[0][UpdateTableEx.INDEX_UNTIL])
    #
    # def get_last_update_time(self, tags: [str]):
    #     record = self.get_update_record(tags)
    #     return None if record is None or len(record) == 0 else text_auto_time(record[0][UpdateTableEx.INDEX_LAST_UPDATE])
    #
    # def get_all_time(self, tags: [str]):
    #     record = self.get_update_record(tags)
    #     return [None, None, None] if len(record) == 0 else \
    #         [text_auto_time(record[0][UpdateTableEx.INDEX_SINCE]),
    #          text_auto_time(record[0][UpdateTableEx.INDEX_UNTIL]),
    #          text_auto_time(record[0][UpdateTableEx.INDEX_LAST_UPDATE])]
    #
    # def update_since(self, tags: [str], since: datetime or str):
    #     return self.__update_date_field(tags, since, UpdateTableEx.INDEX_SINCE, lambda x, y: x < y)
    #
    # def update_until(self, tags: [str], until: datetime or str):
    #     return self.__update_date_field(tags, until, UpdateTableEx.INDEX_UNTIL, lambda x, y: x > y)
    #
    # def update_latest_update_time(self, tags: [str]):
    #     return self.__update_date_field(tags, today(), UpdateTableEx.INDEX_LAST_UPDATE, lambda x, y: x > y)
    #
    # def __update_date_field(self, tags: [str], date: datetime or str, field: int, compare):
    #     joined_tags = self.join_tags(tags)
    #     sql_update = ("UPDATE %s SET %s = '%s' WHERE tags = '%s';" %
    #                   (UpdateTableEx.TABLE, UpdateTableEx.FIELD[field], text_auto_time(date), joined_tags))
    #     sql_insert = ("INSERT INTO %s (tags, %s) VALUES ('%s', '%s');" %
    #                   (UpdateTableEx.TABLE, UpdateTableEx.FIELD[field], joined_tags, text_auto_time(date)))
    #
    #     record = self.get_update_record(tags)
    #     if record is None or len(record) == 0:
    #         return self.__sql_db.QuickExecuteDML(sql_insert, True)
    #     elif record[0][field] is None or compare(text_auto_time(date), text_auto_time(record[0][field])):
    #         return self.__sql_db.QuickExecuteDML(sql_update, True)
    #     else:
    #         return True
    #
    # def get_update_record(self, tags: [str]) -> []:
    #     joined_tags = self.join_tags(tags)
    #     return self.__sql_db.ListFromDB(
    #         UpdateTableEx.TABLE, UpdateTableEx.FIELD, "tags = '%s'" % joined_tags)
    #
    # def delete_update_record(self, tags: [str]):
    #     joined_tags = self.join_tags(tags)
    #     sql_delete = ("DELETE FROM %s WHERE tags = '%s';" % (UpdateTableEx.TABLE, joined_tags))
    #     return self.__sql_db.QuickExecuteDML(sql_delete, True)
    #
    # def join_tags(self, tags: [str]) -> str:
    #     return '.'.join(tags)


# ----------------------------------------------------- Test Code ------------------------------------------------------

# def __default_prepare_test() -> UpdateTableEx:
#     data_path = root_path + '/Data/'
#     sql_db = SqlAccess(data_path + 'sAsUtility.db')
#     ut = UpdateTableEx(sql_db)
#     __clear_test_entry(ut)
#     return ut


def __default_prepare_test() -> UpdateTableEx:
    mongo_db_client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=1000)
    update_table = UpdateTableEx(mongo_db_client, 'TestDB', 'TestTable')
    update_table.clear_update_records()
    return update_table


# def __clear_test_entry(ut: UpdateTableEx):
#     ut.delete_update_record(['__Finance Data', 'Annual', '000001'])
#     ut.delete_update_record(['__Finance Data', 'Annual', '000005'])
#     ut.delete_update_record(['__Index Component', '123456'])
#     ut.delete_update_record(['__Index Component', '567890'])
#     ut.delete_update_record(['__Trade Calender'])
#     ut.delete_update_record(['__Trade News'])


def test_basic_feature():
    ut = __default_prepare_test()

    assert(ut.update_since(['__Finance Data', 'Annual', '000001'], '19900101'))
    assert(ut.update_until(['__Finance Data', 'Annual', '000001'], '20200101'))

    assert(ut.update_since(['__Finance Data', 'Annual', '000005'], '19910202'))
    assert(ut.update_until(['__Finance Data', 'Annual', '000005'], '20210202'))

    assert(ut.update_since(['__Index Component', '123456'], '19920303'))
    assert(ut.update_until(['__Index Component', '123456'], '20220303'))

    assert(ut.update_since(['__Index Component', '567890'], '19930404'))
    assert(ut.update_until(['__Index Component', '567890'], '20230404'))

    assert(ut.update_since(['__Trade Calender'], '19940505'))
    assert(ut.update_until(['__Trade Calender'], '20240505'))

    assert(ut.update_since(['__Trade News'], '19950606'))
    assert(ut.update_until(['__Trade News'], '20250606'))

    # --------------------------------------------------------------------------

    assert(ut.get_since(['__Finance Data', 'Annual', '000001']) == text_auto_time('19900101'))
    assert(ut.get_until(['__Finance Data', 'Annual', '000001']) == text_auto_time('20200101'))

    assert(ut.get_since(['__Finance Data', 'Annual', '000005']) == text_auto_time('19910202'))
    assert(ut.get_until(['__Finance Data', 'Annual', '000005']) == text_auto_time('20210202'))

    assert(ut.get_since(['__Index Component', '123456']) == text_auto_time('19920303'))
    assert(ut.get_until(['__Index Component', '123456']) == text_auto_time('20220303'))

    assert(ut.get_since(['__Index Component', '567890']) == text_auto_time('19930404'))
    assert(ut.get_until(['__Index Component', '567890']) == text_auto_time('20230404'))

    assert(ut.get_since(['__Trade Calender']) == text_auto_time('19940505'))
    assert(ut.get_until(['__Trade Calender']) == text_auto_time('20240505'))

    assert(ut.get_since(['__Trade News']) == text_auto_time('19950606'))
    assert(ut.get_until(['__Trade News']) == text_auto_time('20250606'))

    # --------------------------------------------------------------------------

    ut.delete_update_record(['__Finance Data', 'Annual', '000001'])
    ut.delete_update_record(['__Finance Data', 'Annual', '000005'])
    ut.delete_update_record(['__Index Component', '123456'])
    ut.delete_update_record(['__Index Component', '567890'])
    ut.delete_update_record(['__Trade Calender'])
    ut.delete_update_record(['__Trade News'])

    assert(ut.get_since(['__Finance Data', 'Annual', '000001']) is None)
    assert(ut.get_until(['__Finance Data', 'Annual', '000001']) is None)

    assert(ut.get_since(['__Finance Data', 'Annual', '000005']) is None)
    assert(ut.get_until(['__Finance Data', 'Annual', '000005']) is None)

    assert(ut.get_since(['__Index Component', '123456']) is None)
    assert(ut.get_until(['__Index Component', '123456']) is None)

    assert(ut.get_since(['__Index Component', '567890']) is None)
    assert(ut.get_until(['__Index Component', '567890']) is None)

    assert(ut.get_since(['__Trade Calender']) is None)
    assert(ut.get_until(['__Trade Calender']) is None)

    assert(ut.get_since(['__Trade News']) is None)
    assert(ut.get_until(['__Trade News']) is None)


def test_since_record_unique_and_decrease():
    ut = __default_prepare_test()

    assert(ut.update_since(['__Finance Data', 'Annual', '000001'], '20200101'))
    assert(ut.update_since(['__Finance Data', 'Annual', '000001'], '20000102'))
    assert(ut.update_since(['__Finance Data', 'Annual', '000001'], '20100103'))

    assert(ut.update_since(['__Index Component', '123456'], '20200101'))
    assert(ut.update_since(['__Index Component', '123456'], '20100101'))
    assert(ut.update_since(['__Index Component', '123456'], '20150101'))

    assert(ut.update_since(['__Trade Calender'], '20300101'))
    assert(ut.update_since(['__Trade Calender'], '19900101'))
    assert(ut.update_since(['__Trade Calender'], '19910101'))

    assert(len(ut.get_update_record(['__Finance Data', 'Annual', '000001'])) == 1)
    assert(len(ut.get_update_record(['__Index Component', '123456'])) == 1)
    assert(len(ut.get_update_record(['__Trade Calender'])) == 1)

    assert(ut.get_since(['__Finance Data', 'Annual', '000001']) == text_auto_time('20000102'))
    assert(ut.get_since(['__Index Component', '123456']) == text_auto_time('20100101'))
    assert(ut.get_since(['__Trade Calender']) == text_auto_time('19900101'))


def test_until_record_unique_and_increase():
    ut = __default_prepare_test()

    assert(ut.update_until(['__Finance Data', 'Annual', '000001'], '20200101'))
    assert(ut.update_until(['__Finance Data', 'Annual', '000001'], '20200102'))
    assert(ut.update_until(['__Finance Data', 'Annual', '000001'], '20100103'))

    assert(ut.update_until(['__Index Component', '123456'], '20200101'))
    assert(ut.update_until(['__Index Component', '123456'], '20210101'))
    assert(ut.update_until(['__Index Component', '123456'], '20120101'))

    assert(ut.update_until(['__Trade Calender'], '20300101'))
    assert(ut.update_until(['__Trade Calender'], '20400101'))
    assert(ut.update_until(['__Trade Calender'], '20200101'))

    assert(len(ut.get_update_record(['__Finance Data', 'Annual', '000001'])) == 1)
    assert(len(ut.get_update_record(['__Index Component', '123456'])) == 1)
    assert(len(ut.get_update_record(['__Trade Calender'])) == 1)

    assert(ut.get_until(['__Finance Data', 'Annual', '000001']) == text_auto_time('20200102'))
    assert(ut.get_until(['__Index Component', '123456']) == text_auto_time('20210101'))
    assert(ut.get_until(['__Trade Calender']) == text_auto_time('20400101'))


def test_entry():
    test_basic_feature()
    test_since_record_unique_and_decrease()
    test_until_record_unique_and_increase()


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


sys.excepthook = exception_hook


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass










