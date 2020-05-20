import traceback
from os import sys, path
root_path = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(root_path)

from StockAnalysisSystem.core.DataHub.UniversalDataCenter import *


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
    data_center.register_data_agent(
        DataAgent('test.entry1', DatabaseEntry(), 'test_db', 'test_table'))
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







