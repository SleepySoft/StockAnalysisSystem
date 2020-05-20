from os import sys, path
root_path = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(root_path)

from StockAnalysisSystem.core.Database.NoSqlRw import test_entry as sub_test_entry


def test_entry():
    sub_test_entry()


# ----------------------------------------------------------------------------------------------------------------------

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



