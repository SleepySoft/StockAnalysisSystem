from os import sys, path
root_path = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(root_path)

from StockAnalysisSystem.core.Database.UpdateTableEx import *


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




