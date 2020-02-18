from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    import stock_analysis_system
    from Utiltity.common import *
    from Utiltity.time_utility import *
    from Collector.CollectorUtility import *
except Exception as e:
    sys.path.append(root_path)

    import stock_analysis_system
    from Utiltity.common import *
    from Utiltity.time_utility import *
    from Collector.CollectorUtility import *
finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------

def dump_test_data() -> bool:
    ret = True
    sas = stock_analysis_system.StockAnalysisSystem()
    data_hub = sas.get_data_hub_entry()
    data_center = data_hub.get_data_center()

    df = data_center.query_from_plugin('Market.SecuritiesInfo', '', dump_flag=True)
    if df is None:
        ret = False
        print('Dump Market.SecuritiesInfo Failed.')

    df = data_center.query_from_plugin('Market.TradeCalender', 'A-SHARE',
                                       (default_since(), today()), dump_flag=True)
    if df is None:
        ret = False
        print('Dump Market.TradeCalender Failed.')

    return ret


def test_entry() -> bool:
    ret = True
    sas = stock_analysis_system.StockAnalysisSystem()
    data_hub = sas.get_data_hub_entry()
    data_center = data_hub.get_data_center()

    df = data_center.query_from_plugin('Market.SecuritiesInfo', '', test_flag=True)
    if df is None:
        ret = False
        print('Test Market.SecuritiesInfo Failed.')

    df = data_center.query_from_plugin('Market.TradeCalender', 'A-SHARE',
                                       (default_since(), today()), test_flag=True)
    if df is None:
        ret = False
        print('Test Market.SecuritiesInfo Failed.')

    return ret


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






















