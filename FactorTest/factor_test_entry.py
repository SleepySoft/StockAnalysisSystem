import logging
logging.getLogger('matplotlib').setLevel(logging.WARNING)

import traceback
from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from stock_analysis_system import StockAnalysisSystem
    import FactorTest.test_most_useful_factor as test_most_useful_factor
except Exception as e:
    sys.path.append(root_path)

    from stock_analysis_system import StockAnalysisSystem
    import FactorTest.test_most_useful_factor as test_most_useful_factor
finally:
    pass


def factor_test_entry(sas: StockAnalysisSystem):
    test_most_useful_factor.test_entry(sas)


# ----------------------------------------------------------------------------------------------------------------------

def main():
    sas = StockAnalysisSystem()
    assert sas.check_initialize()

    factor_test_entry(sas)

    print('Process Quit.')


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






