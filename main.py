import sys
import time
import traceback
import tushare as ts
from PyQt5.QtWidgets import QApplication

import main_ui
import config_ui
import stock_analysis_system
from Utiltity.ui_utility import *

# NOTE: If plugin depends on any lib, please import here. Otherwise the packing program cannot find this lib.
# 注意：如果插件依赖于任何库，请务必在这里导入（让打包工具知道有这个依赖项），否则打包后运行可能找不到该库


def run_ui():
    app = QApplication(sys.argv)
    sas = stock_analysis_system.StockAnalysisSystem()

    while not sas.is_initialized():
        dlg = WrapperQDialog(config_ui.ConfigUi())
        dlg.exec()
        sas.check_initialize()

    main_wnd = main_ui.MainWindow()
    main_wnd.show()
    sys.exit(app.exec())


def update_local(update_list: [str], force: bool = False):
    sas = stock_analysis_system.StockAnalysisSystem()
    data_hub = sas.get_data_hub_entry()
    data_center = data_hub.get_data_center()
    data_utility = data_hub.get_data_utility()

    if 'Market.SecuritiesInfo' in update_list:
        print('Updating SecuritiesInfo...')
        data_center.update_local_data('Market.SecuritiesInfo', force=force)

    if 'Market.NamingHistory' in update_list:
        print('Updating Naming History...')
        data_center.update_local_data('Market.NamingHistory', force=force)

    if 'Market.TradeCalender' in update_list:
        print('Updating TradeCalender...')
        data_center.update_local_data('Market.TradeCalender', exchange='SSE', force=force)

    stock_list = data_utility.get_stock_list()

    start_total = time.time()
    print('Updating Finance Data for All A-SHARE Stock.')

    counter = 0
    for stock_identity, name in stock_list:
        start_single = time.time()
        print('Updating Finance Data for ' + stock_identity + ' [' + name + ']')
        if 'Finance.Audit' in update_list:
            data_center.update_local_data('Finance.Audit', stock_identity, force=force)
        if 'Finance.BalanceSheet' in update_list:
            data_center.update_local_data('Finance.BalanceSheet', stock_identity, force=force)
        if 'Finance.IncomeStatement' in update_list:
            data_center.update_local_data('Finance.IncomeStatement', stock_identity, force=force)
        if 'Finance.CashFlowStatement' in update_list:
            data_center.update_local_data('Finance.CashFlowStatement', stock_identity, force=force)

        if 'TradeData.Stock.Daily' in update_list:
            data_center.update_local_data('TradeData.Stock.Daily', stock_identity, force=force)

        if 'Stockholder.PledgeStatus' in update_list:
            data_center.update_local_data('Stockholder.PledgeStatus', stock_identity, force=force)
        if 'Stockholder.PledgeHistory' in update_list:
            data_center.update_local_data('Stockholder.PledgeHistory', stock_identity, force=force)
        if 'Stockholder.Statistics' in update_list:
            data_center.update_local_data('Stockholder.Statistics', stock_identity, force=force)

        counter += 1
        print('Done (%s / %s). Time Spending: %s s' % (counter, len(stock_list), time.time() - start_single))

    if 'Market.IndexInfo' in update_list:
        print('Updating IndexInfo...')
        data_center.update_local_data('Market.IndexInfo', force=force, dump_flag=True)

    from DataHub.DataHubEntry import DEPENDS_INDEX
    # index_list = data_utility.get_index_list()
    index_list = DEPENDS_INDEX

    print('Updating Index Data for All Support Market.')

    counter = 0
    for index_identity, name in index_list:
        start_single = time.time()

        if 'TradeData.Index.Daily' in update_list:
            data_center.update_local_data('TradeData.Index.Daily', index_identity, force=force)

        counter += 1
        print('Done (%s / %s). Time Spending: %s s' % (counter, len(index_list), time.time() - start_single))

    print('Update Finance Data for All A-SHARE Stock Done. Time Spending: ' + str(time.time() - start_total) + 's')


def update_special():
    sas = stock_analysis_system.StockAnalysisSystem()
    data_hub = sas.get_data_hub_entry()
    data_center = data_hub.get_data_center()
    data_utility = data_hub.get_data_utility()

    df1 = data_center.query_from_plugin('Finance.Audit', '000021.SZSE', force=True)
    df2 = data_center.query_from_plugin('Finance.BalanceSheet', '000021.SZSE', force=True)
    df3 = data_center.query_from_plugin('Finance.IncomeStatement', '000021.SZSE', force=True)
    df4 = data_center.query_from_plugin('Finance.CashFlowStatement', '000021.SZSE', force=True)

    print(df1)
    print(df2)
    print(df3)
    print(df4)


def run_strategy():
    pass


def run_console():
    # update_special()
    update_local([
        # 'Market.SecuritiesInfo',
        #
        # 'Market.NamingHistory',
        # 'Market.TradeCalender',
        #
        # 'Finance.Audit',
        # 'Finance.BalanceSheet',
        # 'Finance.IncomeStatement',
        # 'Finance.CashFlowStatement',
        #
        # 'Stockholder.PledgeStatus',
        # 'Stockholder.PledgeHistory',
        # 'Stockholder.Statistics',
        #
        # 'TradeData.Stock.Daily',
        #
        # 'Market.IndexInfo',
        'TradeData.Index.Daily',
    ], True)
    # run_strategy()

    exit(0)


def run_test():
    sas = stock_analysis_system.StockAnalysisSystem()
    data_hub = sas.get_data_hub_entry()
    data_center = data_hub.get_data_center()
    result = data_center.query('Finance.BalanceSheet', '600000.SSE',
                               fields=['存货', '长期待摊费用', '拆出资金'], readable=True)
    assert '存货' in result.columns
    assert '拆出资金' in result.columns
    assert '长期待摊费用' in result.columns
    

def main():
    sas = stock_analysis_system.StockAnalysisSystem()
    sas.check_initialize()

    # run_console()
    run_ui()
    # run_test()

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
