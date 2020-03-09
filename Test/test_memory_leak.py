import gc
import sys
import time
import objgraph
import traceback

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from stock_analysis_system import StockAnalysisSystem
except Exception as e:
    sys.path.append(root_path)
    from stock_analysis_system import StockAnalysisSystem
finally:
    pass


def test_memory_leak_in_update(sas: StockAnalysisSystem):
    sas = StockAnalysisSystem()
    data_hub = sas.get_data_hub_entry()
    data_center = data_hub.get_data_center()
    data_utility = data_hub.get_data_utility()

    # data_center.update_local_data('Market.SecuritiesInfo', force=False)
    # data_center.update_local_data('Market.NamingHistory')
    # data_center.update_local_data('Market.TradeCalender')

    # stock_list = data_utility.get_stock_list()

    # data_center.update_local_data('Finance.Audit', '600000.SSE', force=True)
    # data_center.update_local_data('Finance.Audit', '600036.SSE', force=True)
    #
    # data_center.update_local_data('Finance.BalanceSheet', '600000.SSE', force=True)
    # data_center.update_local_data('Finance.BalanceSheet', '600036.SSE', force=True)
    #
    # data_center.update_local_data('Finance.IncomeStatement', '600000.SSE', force=True)
    # data_center.update_local_data('Finance.IncomeStatement', '600036.SSE', force=True)
    #
    # data_center.update_local_data('Finance.CashFlowStatement', '600000.SSE', force=True)
    # data_center.update_local_data('Finance.CashFlowStatement', '600036.SSE', force=True)

    data_hub = sas.get_data_hub_entry()
    data_center = data_hub.get_data_center()
    data_utility = data_hub.get_data_utility()
    stock_list = data_utility.get_stock_list()

    counter = 0
    for stock_identity, name in stock_list:
        counter += 1
        data_center.update_local_data('Finance.Audit', stock_identity, force=True)
        data_center.update_local_data('Finance.BalanceSheet', stock_identity, force=True)
        data_center.update_local_data('Finance.IncomeStatement', stock_identity, force=True)
        data_center.update_local_data('Finance.CashFlowStatement', stock_identity, force=True)
        data_center.update_local_data('Stockholder.PledgeStatus', stock_identity, force=True)
        data_center.update_local_data('Stockholder.PledgeHistory', stock_identity, force=True)
        if counter > 100:
            break

    print(gc.collect())
    objs = objgraph.by_type('OBJ')
    if len(objs) > 0:
        objgraph.show_backrefs(objs[0], max_depth=10, filename='obj.dot')

    return True


def test_entry() -> bool:
    sas = StockAnalysisSystem()
    if not sas.check_initialize():
        print('StockAnalysisSystem init fail.')
        return False
    test_memory_leak_in_update(sas)
    return True


def main():
    assert test_entry()


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
