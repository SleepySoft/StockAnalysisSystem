import sys
import traceback

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Utiltity.time_utility import *
    from Database.DatabaseEntry import DatabaseEntry
except Exception as e:
    sys.path.append(root_path)

    from Utiltity.time_utility import *
    from Database.DatabaseEntry import DatabaseEntry
finally:
    pass


class UpdateTable:
    TABLE = 'UpdateTable'
    FIELD = ['Serial', 'L1Tag', 'L2Tag', 'L3Tag', 'Since', 'Until', 'LastUpdate']
    INDEX_SINCE = 4
    INDEX_UNTIL = 5
    INDEX_LAST_UPDATE = 6

    def __init__(self):
        pass

    def get_since(self, tag1: str, tag2: str, tag3: str):
        record = self.get_update_record(tag1, tag2, tag3)
        return None if len(record) == 0 else text_auto_time(record[0][UpdateTable.INDEX_SINCE])

    def get_until(self, tag1: str, tag2: str, tag3: str):
        record = self.get_update_record(tag1, tag2, tag3)
        return None if len(record) == 0 else text_auto_time(record[0][UpdateTable.INDEX_UNTIL])

    def get_since_until(self, tag1: str, tag2: str, tag3: str):
        record = self.get_update_record(tag1, tag2, tag3)
        return None if len(record) == 0 else text_auto_time(record[0][UpdateTable.INDEX_SINCE]), \
               None if len(record) == 0 else text_auto_time(record[0][UpdateTable.INDEX_UNTIL])

    def get_last_update_time(self, tag1: str, tag2: str, tag3: str):
        record = self.get_update_record(tag1, tag2, tag3)
        return None if record is None or len(record) == 0 else text_auto_time(record[0][UpdateTable.INDEX_LAST_UPDATE])

    def get_all_time(self, tag1: str, tag2: str, tag3: str):
        record = self.get_update_record(tag1, tag2, tag3)
        return [None, None, None] if len(record) == 0 else \
            [text_auto_time(record[0][UpdateTable.INDEX_SINCE]),
             text_auto_time(record[0][UpdateTable.INDEX_UNTIL]),
             text_auto_time(record[0][UpdateTable.INDEX_LAST_UPDATE])]

    def update_since(self, tag1: str, tag2: str, tag3: str, since: datetime or str):
        return self.__update_date_field(tag1, tag2, tag3, since, UpdateTable.INDEX_SINCE, lambda x, y: x < y)

    def update_until(self, tag1: str, tag2: str, tag3: str, until: datetime or str):
        return self.__update_date_field(tag1, tag2, tag3, until, UpdateTable.INDEX_UNTIL, lambda x, y: x > y)

    def update_latest_update_time(self, tag1: str, tag2: str, tag3: str):
        return self.__update_date_field(tag1, tag2, tag3, today(), UpdateTable.INDEX_LAST_UPDATE, lambda x, y: x > y)

    def __update_date_field(self, tag1: str, tag2: str, tag3: str, date: datetime or str, field: int, compare):
        sql_update = ("UPDATE %s SET %s = '%s' WHERE L1Tag='%s' AND L2Tag='%s' AND L3Tag='%s';" %
                      (UpdateTable.TABLE, UpdateTable.FIELD[field], text_auto_time(date), tag1, tag2, tag3))
        sql_insert = ("INSERT INTO %s (L1Tag, L2Tag, L3Tag, %s) VALUES ('%s', '%s', '%s', '%s');" %
                      (UpdateTable.TABLE, UpdateTable.FIELD[field], tag1, tag2, tag3, text_auto_time(date)))

        record = self.get_update_record(tag1, tag2, tag3)
        if record is None or len(record) == 0:
            return DatabaseEntry().get_utility_db().QuickExecuteDML(sql_insert, True)
        elif record[0][field] is None or compare(text_auto_time(date), text_auto_time(record[0][field])):
            return DatabaseEntry().get_utility_db().QuickExecuteDML(sql_update, True)
        else:
            return True

    def get_update_record(self, tag1: str, tag2: str, tag3: str) -> []:
        return DatabaseEntry().get_utility_db().ListFromDB(
            UpdateTable.TABLE, UpdateTable.FIELD, "L1Tag = '%s' AND L2Tag = '%s' AND L3Tag = '%s'" % (tag1, tag2, tag3))

    def delete_update_record(self, tag1: str, tag2: str, tag3: str):
        sql_delete = ("DELETE FROM %s WHERE  L1Tag='%s' AND L2Tag='%s' AND L3Tag='%s';" %
                      (UpdateTable.TABLE, tag1, tag2, tag3))
        return DatabaseEntry().get_utility_db().QuickExecuteDML(sql_delete, True)


# ----------------------------------------------------- Test Code ------------------------------------------------------


def __clear_test_entry(ut: UpdateTable):
    ut.delete_update_record('__Finance Data', 'Annual', '000001')
    ut.delete_update_record('__Finance Data', 'Annual', '000005')
    ut.delete_update_record('__Index Component', '123456', '')
    ut.delete_update_record('__Index Component', '567890', '')
    ut.delete_update_record('__Trade Calender', '', '')
    ut.delete_update_record('__Trade News', '', '')


def test_basic_feature():
    ut = UpdateTable()
    __clear_test_entry(ut)

    assert(ut.update_since('__Finance Data', 'Annual', '000001', '19900101'))
    assert(ut.update_until('__Finance Data', 'Annual', '000001', '20200101'))

    assert(ut.update_since('__Finance Data', 'Annual', '000005', '19910202'))
    assert(ut.update_until('__Finance Data', 'Annual', '000005', '20210202'))

    assert(ut.update_since('__Index Component', '123456', '', '19920303'))
    assert(ut.update_until('__Index Component', '123456', '', '20220303'))

    assert(ut.update_since('__Index Component', '567890', '', '19930404'))
    assert(ut.update_until('__Index Component', '567890', '', '20230404'))

    assert(ut.update_since('__Trade Calender', '', '', '19940505'))
    assert(ut.update_until('__Trade Calender', '', '', '20240505'))

    assert(ut.update_since('__Trade News', '', '', '19950606'))
    assert(ut.update_until('__Trade News', '', '', '20250606'))

    # --------------------------------------------------------------------------

    assert(ut.get_since('__Finance Data', 'Annual', '000001') == text_auto_time('19900101'))
    assert(ut.get_until('__Finance Data', 'Annual', '000001') == text_auto_time('20200101'))

    assert(ut.get_since('__Finance Data', 'Annual', '000005') == text_auto_time('19910202'))
    assert(ut.get_until('__Finance Data', 'Annual', '000005') == text_auto_time('20210202'))

    assert(ut.get_since('__Index Component', '123456', '') == text_auto_time('19920303'))
    assert(ut.get_until('__Index Component', '123456', '') == text_auto_time('20220303'))

    assert(ut.get_since('__Index Component', '567890', '') == text_auto_time('19930404'))
    assert(ut.get_until('__Index Component', '567890', '') == text_auto_time('20230404'))

    assert(ut.get_since('__Trade Calender', '', '') == text_auto_time('19940505'))
    assert(ut.get_until('__Trade Calender', '', '') == text_auto_time('20240505'))

    assert(ut.get_since('__Trade News', '', '') == text_auto_time('19950606'))
    assert(ut.get_until('__Trade News', '', '') == text_auto_time('20250606'))

    # --------------------------------------------------------------------------

    ut.delete_update_record('__Finance Data', 'Annual', '000001')
    ut.delete_update_record('__Finance Data', 'Annual', '000005')
    ut.delete_update_record('__Index Component', '123456', '')
    ut.delete_update_record('__Index Component', '567890', '')
    ut.delete_update_record('__Trade Calender', '', '')
    ut.delete_update_record('__Trade News', '', '')

    assert(ut.get_since('__Finance Data', 'Annual', '000001') is None)
    assert(ut.get_until('__Finance Data', 'Annual', '000001') is None)

    assert(ut.get_since('__Finance Data', 'Annual', '000005') is None)
    assert(ut.get_until('__Finance Data', 'Annual', '000005') is None)

    assert(ut.get_since('__Index Component', '123456', '') is None)
    assert(ut.get_until('__Index Component', '123456', '') is None)

    assert(ut.get_since('__Index Component', '567890', '') is None)
    assert(ut.get_until('__Index Component', '567890', '') is None)

    assert(ut.get_since('__Trade Calender', '', '') is None)
    assert(ut.get_until('__Trade Calender', '', '') is None)

    assert(ut.get_since('__Trade News', '', '') is None)
    assert(ut.get_until('__Trade News', '', '') is None)

    __clear_test_entry(ut)


def test_since_record_unique_and_decrease():
    ut = UpdateTable()
    __clear_test_entry(ut)

    assert(ut.update_since('__Finance Data', 'Annual', '000001', '20200101'))
    assert(ut.update_since('__Finance Data', 'Annual', '000001', '20000102'))
    assert(ut.update_since('__Finance Data', 'Annual', '000001', '20100103'))

    assert(ut.update_since('__Index Component', '123456', '', '20200101'))
    assert(ut.update_since('__Index Component', '123456', '', '20100101'))
    assert(ut.update_since('__Index Component', '123456', '', '20150101'))

    assert(ut.update_since('__Trade Calender', '', '', '20300101'))
    assert(ut.update_since('__Trade Calender', '', '', '19900101'))
    assert(ut.update_since('__Trade Calender', '', '', '19910101'))

    assert(len(ut.get_update_record('__Finance Data', 'Annual', '000001')) == 1)
    assert(len(ut.get_update_record('__Index Component', '123456', '')) == 1)
    assert(len(ut.get_update_record('__Trade Calender', '', '')) == 1)

    assert(ut.get_since('__Finance Data', 'Annual', '000001') == text_auto_time('20000102'))
    assert(ut.get_since('__Index Component', '123456', '') == text_auto_time('20100101'))
    assert(ut.get_since('__Trade Calender', '', '') == text_auto_time('19900101'))

    __clear_test_entry(ut)


def test_until_record_unique_and_increase():
    ut = UpdateTable()
    __clear_test_entry(ut)

    assert(ut.update_until('__Finance Data', 'Annual', '000001', '20200101'))
    assert(ut.update_until('__Finance Data', 'Annual', '000001', '20200102'))
    assert(ut.update_until('__Finance Data', 'Annual', '000001', '20100103'))

    assert(ut.update_until('__Index Component', '123456', '', '20200101'))
    assert(ut.update_until('__Index Component', '123456', '', '20210101'))
    assert(ut.update_until('__Index Component', '123456', '', '20120101'))

    assert(ut.update_until('__Trade Calender', '', '', '20300101'))
    assert(ut.update_until('__Trade Calender', '', '', '20400101'))
    assert(ut.update_until('__Trade Calender', '', '', '20200101'))

    assert(len(ut.get_update_record('__Finance Data', 'Annual', '000001')) == 1)
    assert(len(ut.get_update_record('__Index Component', '123456', '')) == 1)
    assert(len(ut.get_update_record('__Trade Calender', '', '')) == 1)

    assert(ut.get_until('__Finance Data', 'Annual', '000001') == text_auto_time('20200102'))
    assert(ut.get_until('__Index Component', '123456', '') == text_auto_time('20210101'))
    assert(ut.get_until('__Trade Calender', '', '') == text_auto_time('20400101'))

    __clear_test_entry(ut)


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










