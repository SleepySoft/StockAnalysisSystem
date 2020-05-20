import traceback
import pandas as pd
from os import sys, path
root_path = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(root_path)

from StockAnalysisSystem.core.Utiltity.df_utility import check_date_continuity
from StockAnalysisSystem.core.Utiltity.df_utility import test_entry as test_entry_df_utility


def test_check_date_continuity():
    df = pd.read_csv(root_path + '/TestData/Market_TradeCalender.csv')
    continuity, min_date, max_date = check_date_continuity(df, 'cal_date')
    print('continuity = ' + str(continuity))
    print('min_date = ' + str(min_date))
    print('max_date = ' + str(max_date))


def test_entry():
    test_entry_df_utility()
    test_check_date_continuity()


def main():
    test_entry()
    print('All Test Passed.')


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









