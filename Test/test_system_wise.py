from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Utiltity.common import *
    from Utiltity.time_utility import *
    from Collector.CollectorUtility import *
    from stock_analysis_system import StockAnalysisSystem
except Exception as e:
    sys.path.append(root_path)

    from Utiltity.common import *
    from Utiltity.time_utility import *
    from Collector.CollectorUtility import *
    from stock_analysis_system import StockAnalysisSystem
finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------

def test_all_update(sas: StockAnalysisSystem):
    data_hub = sas.get_data_hub_entry()
    data_center = data_hub.get_data_center()
    data_utility = data_hub.get_data_utility()

    assert data_center.update_local_data('Market.SecuritiesInfo', force=True)
    assert data_center.update_local_data('Market.NamingHistory', force=True)
    assert data_center.update_local_data('Market.TradeCalender', exchange='SSE', force=True)

    assert data_center.update_local_data('Finance.Audit', '600000')
    assert data_center.update_local_data('Finance.BalanceSheet', '600000')
    assert data_center.update_local_data('Finance.IncomeStatement', '600000')
    assert data_center.update_local_data('Finance.CashFlowStatement', '600000')

    return True


def test_memory_leak(sas: StockAnalysisSystem):
    data_hub = sas.get_data_hub_entry()
    data_center = data_hub.get_data_center()
    data_utility = data_hub.get_data_utility()

    assert data_center.update_local_data('Finance.Audit', '600000')
    assert data_center.update_local_data('Finance.Audit', '600036')


def test_entry() -> bool:
    sas = StockAnalysisSystem()
    if not sas.check_initialize():
        print('StockAnalysisSystem initialize fail.')
        return False
    assert test_all_update()


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


