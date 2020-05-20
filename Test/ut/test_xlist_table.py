from os import sys, path
root_path = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(root_path)

from StockAnalysisSystem.core.Database.XListTable import *


# ----------------------------------------------------------------------------------------------------------------------

def __prepare_x_table(name: str) -> XListTable:
    data_path = root_path + '/Temporary/'
    sql_db = SqlAccess(data_path + 'sAsUtility.db')
    x_table = XListTable(name, sql_db)
    return x_table


def test_basic():
    x_table = __prepare_x_table('GrayTable')
    x_table.clear()
    x_table.flush()

    x_table.upsert_to_list('100000.SSZ', 'reason1', 'comments1')
    x_table.upsert_to_list('100000.SSZ', 'reason2', 'comments2')
    x_table.upsert_to_list('100000.SSZ', 'reason3', 'comments3')

    df = x_table.get_name_table()
    assert len(df) == 1

    line = df.iloc[0].values.tolist()
    assert line[0] == '100000.SSZ'
    assert line[1] == 'reason3'
    assert line[2] == 'comments3'
    print('Last update: ' + str(line[3]))

    x_table.upsert_to_list('100001.SSZ', 'reason5', 'comments5')
    x_table.upsert_to_list('100002.SSZ', 'reason6', 'comments6')
    x_table.upsert_to_list('100003.SSZ', 'reason7', 'comments7')
    x_table.upsert_to_list('100003.SSZ', 'reason8', 'comments8')
    x_table.upsert_to_list('100004.SSZ', 'reason8', 'comments8')
    x_table.flush()

    x_table.clear()
    x_table.reload()

    df = x_table.get_name_table()
    assert len(df) == 5


def test_entry():
    test_basic()


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

