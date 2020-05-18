import sys
import traceback

from stock_analysis_system import StockAnalysisSystem
from FactorTest.factor_test_entry import factor_test_entry

sasEntry = None
data_center = None
data_utility = None
factor_center = None


def test_fetch_data():
    assert data_center.update_local_data('Market.SecuritiesInfo', force=True)
    assert data_center.update_local_data('Market.IndexInfo', force=True)
    assert data_center.update_local_data('Market.TradeCalender', exchange='SSE', force=True)
    assert data_center.update_local_data('Market.NamingHistory', force=True)

    stock_list = data_utility.get_stock_list()
    assert len(stock_list) > 3000

    assert data_center.update_local_data('Market.SecuritiesTags', stock_list[0])

    assert data_center.update_local_data('Finance.Audit', stock_list[0], force=True)
    assert data_center.update_local_data('Finance.BalanceSheet', stock_list[0], force=True)
    assert data_center.update_local_data('Finance.IncomeStatement', stock_list[0], force=True)
    assert data_center.update_local_data('Finance.CashFlowStatement', stock_list[0], force=True)
    assert data_center.update_local_data('Finance.BusinessComposition', stock_list[0], force=True)

    assert data_center.update_local_data('Stockholder.PledgeStatus', stock_list[0], force=True)
    assert data_center.update_local_data('Stockholder.PledgeHistory', stock_list[0], force=True)
    assert data_center.update_local_data('Stockholder.Statistics', stock_list[0], force=True)

    assert data_center.update_local_data('TradeData.Stock.Daily', stock_list[0], force=True)
    assert data_center.update_local_data('TradeData.Index.Daily', '000001.SSE', force=True)


def test_factors():
    factor_test_entry()


def test_entry():
    test_fetch_data()
    test_factors()


# ----------------------------------------------------------------------------------------------------------------------


def main():
    global sasEntry
    global data_center
    global data_utility
    global factor_center

    sasEntry = StockAnalysisSystem()
    assert StockAnalysisSystem().check_initialize()

    data_center = sasEntry.get_data_hub_entry().get_data_center()
    data_utility = sasEntry.get_data_hub_entry().get_data_utility()
    factor_center = sasEntry.get_factor_center()

    test_entry()

    print('All test passed.')


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
