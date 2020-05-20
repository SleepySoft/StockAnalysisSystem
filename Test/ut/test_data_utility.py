import traceback
from os import sys, path
root_path = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(root_path)

from StockAnalysisSystem.core.DataHub.DataUtility import *


# ----------------------------------------------------------------------------------------------------------------------
#                                                         Test
# ----------------------------------------------------------------------------------------------------------------------

def test_identity_name_info_cache():
    cache = IdentityNameInfoCache()

    cache.set_id_name('id_1', 'id_1_name_1')
    cache.set_id_name('id_1', 'id_1_name_1')
    cache.set_id_name('id_1', 'id_1_name_2')
    cache.set_id_name('id_1', 'id_1_name_3')
    cache.set_id_info('id_1', 'date', datetime.date(1990, 1, 1))
    cache.set_id_info('id_1', 'date', datetime.date(2000, 2, 2))
    cache.set_id_info('id_1', 'key1', 'value1')
    cache.set_id_info('id_1', 'key2', 'value2')
    cache.set_id_info('id_1', 'key3', 'value3')

    cache.set_id_name('id_2', 'id_2_name_1')
    cache.set_id_name('id_2', 'id_2_name_2')
    cache.set_id_name('id_2', 'id_2_name_3')
    cache.set_id_info('id_2', 'date', datetime.date(2010, 10, 10))

    # ---------------- Test Ids -----------------

    assert 'id_1' in cache.get_ids()
    assert 'id_2' in cache.get_ids()

    # ---------------- Test name ----------------

    # No duplicate names
    id_1_names = cache.id_to_names('id_1')
    assert len(id_1_names) == 3
    assert 'id_1_name_1' in id_1_names
    assert 'id_1_name_2' in id_1_names
    assert 'id_1_name_3' in id_1_names

    # Normal case
    id_2_names = cache.id_to_names('id_2')
    assert len(id_2_names) == 3

    # If id not exits, returns ['']
    id_3_names = cache.id_to_names('id_3')
    assert len(id_3_names) == 1
    assert id_3_names[0] == ''

    # ---------------- Test Info ----------------

    # Should keep the last set info
    assert cache.get_id_info('id_1', 'date') == datetime.date(2000, 2, 2)

    # Should keep the order of query keys
    # Return default value if info not exists
    info = cache.get_id_info('id_1', ['key3', 'key_x', 'key1', 'key2'], 'NotExists')
    assert info[0] == 'value3'
    assert info[1] == 'NotExists'
    assert info[2] == 'value1'
    assert info[3] == 'value2'


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    test_identity_name_info_cache()

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

