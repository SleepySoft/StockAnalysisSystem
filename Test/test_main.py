from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    import Test.test_market_data
    import Test.test_finance_data
except Exception as e:
    sys.path.append(root_path)

finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------

def test_entry() -> bool:
    if Test.test_market_data.test_entry() and \
            Test.test_finance_data.test_entry():
        print('All test passed.')
        return True
    else:
        print('Test failed.')
        return False


def main():
    test_entry()


# ----------------------------------------------------------------------------------------------------------------------

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






















